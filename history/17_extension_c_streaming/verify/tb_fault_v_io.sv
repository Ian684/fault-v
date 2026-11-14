`timescale 1ns/1ps
module tb_fault_v_io;
    logic clk=0,rst=1,req_valid=0,req_write=0,rsp_ready=0;
    logic [31:0] req_addr=0,req_wdata=0;
    logic [3:0] req_wstrb=0;
    logic [1:0] gpio_in=2;
    wire req_ready,rsp_valid,rsp_err,uart_tx;
    wire [31:0] rsp_data;
    wire [3:0] gpio_out;
    integer tests=0,stalls=0,received=0;
    always #5 clk=~clk;
    fault_v_io #(.UART_CLKS_PER_BIT(8)) dut(.*);
    task automatic must(input logic good,input string text);
        if(good!==1'b1)$fatal(1,"FAIL IO: %s",text);
    endtask
    task automatic transaction(input logic wr,input logic[31:0] addr,data,
        input logic[3:0] mask,input logic error,input logic[31:0] expected);
        @(negedge clk);req_valid=1;req_write=wr;req_addr=addr;req_wdata=data;req_wstrb=mask;
        @(posedge clk);
        while(!req_ready) begin stalls++;@(posedge clk);end
        @(negedge clk);req_valid=0;
        must(rsp_valid && rsp_err==error && rsp_data===expected,"response");
        repeat(3) begin @(posedge clk);#1;
            must(rsp_valid && rsp_err==error && rsp_data===expected && !req_ready,"response held under backpressure");
        end
        @(negedge clk);rsp_ready=1;
        @(posedge clk);@(negedge clk);rsp_ready=0;
        must(!rsp_valid,"response consumed once");
        tests++;$display("PASS IO %0d addr=%h write=%b error=%b",tests,addr,wr,error);
    endtask
    task automatic receive_byte(input logic [7:0] expected);
        logic[7:0] actual;
        @(negedge uart_tx);#40;must(uart_tx==0,"start bit");
        #80;
        for(integer b=0;b<8;b++) begin actual[b]=uart_tx;#80;end
        must(uart_tx==1,"stop bit");must(actual==expected,"LSB first byte");
        received++;$display("PASS serial byte=%h",actual);
    endtask
    initial begin
        fork begin receive_byte(8'ha5);receive_byte(8'h3c);end join_none
        repeat(3) @(posedge clk);@(negedge clk);rst=0;
        transaction(0,32'h20000104,0,0,0,1);
        transaction(0,32'h20000200,0,0,0,0);
        transaction(1,32'h20000200,32'hfffffffA,15,0,0);
        must(gpio_out==10,"GPIO low four bits");
        transaction(0,32'h20000200,0,0,0,10);
        transaction(0,32'h20000204,0,0,0,2);
        transaction(1,32'h20000204,0,15,1,0);
        transaction(1,32'h20000200,0,1,1,0);must(gpio_out==10,"bad mask has no side effect");
        transaction(0,32'h20000100,0,0,1,0);
        transaction(1,32'h20000104,0,15,1,0);
        transaction(0,32'h20000108,0,0,1,0);
        transaction(0,32'h20000201,0,0,1,0);
        transaction(1,32'h20000100,8'ha5,15,0,0);
        transaction(0,32'h20000104,0,0,0,2);
        transaction(1,32'h20000100,8'h3c,15,0,0);
        must(stalls>0,"busy UART write stalls");
        wait(received==2);wait(!dut.tx_busy);
        transaction(0,32'h20000104,0,0,0,1);
        transaction(1,32'h20000100,8'h55,15,0,0);
        must(dut.tx_busy,"active frame before reset");
        @(negedge clk);rst=1;@(posedge clk);#1;
        must(uart_tx==1 && !dut.tx_busy && gpio_out==0 && !rsp_valid,"reset aborts frame and clears outputs");
        @(negedge clk);rst=0;repeat(12)@(posedge clk);
        must(uart_tx==1,"idle after reset");
        must(tests==16,"transaction count");
        $display("ALL 16 IO TRANSACTIONS PASSED; 2 SERIAL BYTES PASSED; stalls=%0d",stalls);$finish;
    end
    initial begin #20000;$fatal(1,"IO timeout");end
endmodule
