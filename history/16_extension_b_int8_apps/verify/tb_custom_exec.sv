`timescale 1ns/1ps
module tb_custom_exec;
    import fault_v_pkg::*;
    logic clk=0,rst=1,req_valid=0,rsp_ready=0;
    logic [31:0] req_a=0,req_b=0,req_acc=0,rsp_result;
    custom_op_t req_op=CUSTOM_DOT4;
    wire req_ready,rsp_valid;
    always #5 clk=~clk;
    custom_exec dut(.*);
    integer passed=0,aborts=0,accepted=0,responses=0;
    task automatic must(input logic ok,input string msg);
        if(ok!==1'b1)$fatal(1,"FAIL custom unit case=%0d: %s",passed,msg);
    endtask
    always @(posedge clk) if(!rst) begin
        if(req_valid && req_ready)accepted++;
        if(rsp_valid && rsp_ready)responses++;
    end
    task automatic operation(input integer op,input logic [31:0] a,b,acc,want,input integer hold_cycles);
        integer latency;
        @(negedge clk);must(req_ready && !rsp_valid,"idle before request");
        req_op=custom_op_t'(op);req_a=a;req_b=b;req_acc=acc;req_valid=1;rsp_ready=0;
        @(posedge clk);#1;must(!req_ready,"accepted once");
        @(negedge clk);req_valid=0;req_a=~a;req_b=~b;req_acc=~acc;req_op=CUSTOM_QNT8;
        latency=0;
        while(!rsp_valid)begin @(posedge clk);#1;latency++;must(latency<=5,"bounded completion");end
        must(latency==((op==8 || op==10)?2:1),"unit latency");
        must(rsp_result===want,"reference result");
        // A queued request must not overwrite a held response.
        @(negedge clk);req_valid=1;
        repeat(hold_cycles)begin
            @(posedge clk);#1;must(rsp_valid && rsp_result===want && !req_ready,"response backpressure stable");
        end
        @(negedge clk);req_valid=0;rsp_ready=1;
        @(posedge clk);#1;must(req_ready && !rsp_valid,"response consumed exactly once");
        @(negedge clk);rsp_ready=0;passed++;
    endtask
    task automatic cancel(input integer op,input integer cycles);
        @(negedge clk);req_op=custom_op_t'(op);req_a=32'h80808080;req_b=32'h7f7f7f7f;req_valid=1;
        @(posedge clk);@(negedge clk);req_valid=0;
        repeat(cycles)@(posedge clk);
        @(negedge clk);rst=1;#1;
        must(!req_ready && !rsp_valid,"reset gates channels");
        @(posedge clk);#1;must(rsp_result==0,"reset clears result");
        @(negedge clk);rst=0;
        repeat(7)begin @(posedge clk);#1;must(req_ready && !rsp_valid,"no stale response after reset");end
        aborts++;
        operation(0,32'h04030201,32'h08070605,0,70,2);
    endtask
    integer fd,rows,scanned,op;
    logic [31:0] av,bv,cv,expected;
    initial begin
        repeat(3)@(posedge clk);@(negedge clk);rst=0;
        fd=$fopen("../verify/unit.vec","r");must(fd!=0,"open reference vectors");
        scanned=$fscanf(fd,"%d",rows);must(scanned==1,"vector count");
        for(integer i=0;i<rows;i++)begin
            scanned=$fscanf(fd,"%d %h %h %h %h",op,av,bv,cv,expected);must(scanned==5,"vector row");
            operation(op,av,bv,cv,expected,i%7);
        end
        $fclose(fd);
        for(integer k=0;k<12;k++)for(integer c=0;c<=((k==8 || k==10)?2:1);c++)cancel(k,c);
        // Reset with req_valid asserted must not accept a request.
        @(negedge clk);rst=1;req_valid=1;
        @(posedge clk);#1;must(!req_ready && !rsp_valid,"request not accepted during reset");
        @(negedge clk);req_valid=0;rst=0;
        repeat(7)begin @(posedge clk);#1;must(!rsp_valid,"reset request absent");end
        must(accepted==responses+aborts,"accepted = completed + canceled");
        $display("ALL %0d CUSTOM UNIT RESULTS PASSED; %0d RESET CANCELLATIONS; requests=%0d responses=%0d",passed,aborts,accepted,responses);
        $finish;
    end
    initial begin #500000000;$fatal(1,"Custom unit timeout");end
endmodule

