`timescale 1ns/1ps
module tb_payload;
    logic clk=0,resetn=0,run=0,btn_reset=0;
    logic [1:0] sw=1;
    wire [3:0] led;
    wire uart_tx;
    wire [31:0] debug_status;
    integer bytes=0;
    string text="C OK";
    always #10 clk=~clk;
    fault_v_payload_impl dut(.*);
    task automatic must(input logic ok,input string message);
        if(ok!==1'b1)$fatal(1,"FAIL payload: %s",message);
    endtask
    initial forever begin
        logic[7:0] value;
        @(negedge uart_tx);#4340;must(!uart_tx,"start bit");#8680;
        for(integer b=0;b<8;b++)begin value[b]=uart_tx;#8680;end
        must(uart_tx,"stop bit");
        if(bytes%6<4)must(value==text.getc(bytes%6),"text byte");
        else must(value==(bytes%6==4?8'h0d:8'h0a),"CR/LF");
        bytes++;
    end
    task automatic complete(input integer round_id);
        wait(debug_status[2]);#1;
        must(debug_status[1:0]==1 && debug_status[12:9]==9,"success debug status");
        must(bytes==round_id*6 && led==5,"UART count and LED");
        $display("PASS PAYLOAD run=%0d bytes=%0d debug=%h LED=%h",round_id,bytes,debug_status,led);
    endtask
    initial begin
        repeat(5)@(posedge clk);@(negedge clk);resetn=1;
        #11000000;
        must(dut.rst && !debug_status[2] && led==0,"ARM run=0 holds CPU reset");
        @(negedge clk);run=1;complete(1);
        @(negedge clk);run=0;repeat(10)@(posedge clk);#1;
        must(led==0 && debug_status==0,"ARM stop resets CPU");
        @(negedge clk);run=1;complete(2);
        @(negedge clk);btn_reset=1;repeat(10)@(posedge clk);#1;
        must(led==0 && debug_status==0,"button resets CPU");
        @(negedge clk);btn_reset=0;complete(3);
        $display("ALL 3 PAYLOAD RUNS PASSED; 18 UART BYTES; ARM CONTROL AND BUTTON RESET");$finish;
    end
    initial begin #120000000;$fatal(1,"Payload timeout");end
endmodule

