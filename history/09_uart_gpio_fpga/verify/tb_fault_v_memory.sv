module tb_fault_v_memory;
    timeunit 1ns; timeprecision 1ps;
    logic clk=0,rst=1,req_valid=0,req_ready,req_write=0,rsp_valid,rsp_ready=0,rsp_err;
    logic [31:0] req_addr=0,req_wdata=0,rsp_data,program_status;
    logic [3:0] req_wstrb=0;
    integer checks=0;
    logic ro_req_ready,ro_rsp_valid,ro_rsp_err;
    logic [31:0] ro_rsp_data,ro_status;
    always #5 clk=~clk;
    fault_v_memory #(.WORDS(4096),.WITH_STATUS(1),.RESPONSE_DELAY(3)) dut(.*);
    fault_v_memory #(.WORDS(4096),.READ_ONLY(1),.RESPONSE_DELAY(3)) rom(
        .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(ro_req_ready),.req_write(req_write),
        .req_addr(req_addr),.req_wdata(req_wdata),.req_wstrb(req_wstrb),
        .rsp_valid(ro_rsp_valid),.rsp_ready(rsp_ready),.rsp_data(ro_rsp_data),.rsp_err(ro_rsp_err),.program_status(ro_status));
    task automatic must(input logic condition,input string label_text);
        if (condition!==1'b1) $fatal(1,"FAIL memory %s",label_text);
    endtask
    task automatic transact(input logic wr,input logic [31:0] addr,data,input logic [3:0] mask,
                            input logic err,input logic [31:0] expected);
        @(negedge clk); req_valid=1; req_write=wr; req_addr=addr; req_wdata=data; req_wstrb=mask;
        @(posedge clk); must(req_ready,"accept request"); #1;
        @(negedge clk); req_valid=0;
        while (!rsp_valid) begin @(posedge clk); #1; end
        repeat(3) begin
            must(!req_ready && rsp_valid && rsp_err===err && rsp_data===expected,"held response under backpressure");
            must(!ro_req_ready && ro_rsp_valid && ro_rsp_data==0,"read-only RAM response held and contents unchanged");
            must(ro_rsp_err==(wr || addr<32'h10000000 || addr>=32'h10004000 || addr[1:0]!=0),"read-only RAM rejects writes and invalid addresses");
            @(posedge clk); #1;
        end
        @(negedge clk); rsp_ready=1;
        @(posedge clk); #1; must(!rsp_valid,"response consumed once");
        @(negedge clk); rsp_ready=0;
        checks=checks+1; $display("PASS memory %0d addr=%h wr=%0d error=%0d",checks,addr,wr,err);
    endtask
    initial begin
        repeat(2) begin @(posedge clk); #1; end
        @(negedge clk); rst=0;
        transact(1,32'h10000000,32'h89abcdef,4'hf,0,0);
        transact(0,32'h10000000,0,0,0,32'h89abcdef);
        transact(1,32'h10000000,32'h00005500,4'h2,0,32'h89abcdef);
        transact(0,32'h10000000,0,0,0,32'h89ab55ef);
        transact(1,32'h10003ffc,32'h12345678,4'hf,0,0);
        transact(0,32'h10003ffc,0,0,0,32'h12345678);
        transact(1,32'h10004000,32'hffffffff,4'hf,1,0);
        transact(0,32'h10000001,0,0,1,0);
        transact(1,32'h20000000,1,4'hf,0,0);
        transact(0,32'h20000000,0,0,0,1);
        transact(1,32'h20000000,99,4'h1,1,0);
        transact(0,32'h20000000,0,0,0,1);
        transact(0,32'h20000004,0,0,1,0);
        // Write is committed at acceptance; reset cancels only its outstanding response.
        @(negedge clk); req_valid=1; req_write=1; req_addr=32'h10000004; req_wdata=32'habcdef01; req_wstrb=4'hf;
        @(posedge clk); must(req_ready,"accepted write before reset"); #1;
        @(negedge clk); req_valid=0; rst=1;
        @(posedge clk); #1;
        must(!rsp_valid && program_status==0,"reset cancels response and clears status");
        @(negedge clk); rst=0;
        transact(0,32'h10000004,0,0,0,32'habcdef01);
        transact(0,32'h10003ffc,0,0,0,32'h12345678);
        transact(0,32'h20000000,0,0,0,0);
        $display("ALL 16 MEMORY ENDPOINT TRANSACTIONS PASSED"); $finish;
    end
    initial begin #20000; $fatal(1,"GLOBAL TIMEOUT MEMORY ENDPOINT"); end
endmodule
