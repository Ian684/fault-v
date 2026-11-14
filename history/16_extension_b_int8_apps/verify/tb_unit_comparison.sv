`timescale 1ns/1ps
module tb_unit_comparison;
 import fault_v_pkg::*;
 logic clk=0,rst=1,req_valid=0,rsp_ready=0;always #5 clk=~clk;
 custom_op_t req_op;
 logic [31:0] req_a,req_b;
 wire [1:0] req_ready,rsp_valid;wire [31:0] result[0:1];
 custom_exec_shared shared(.clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready[0]),.req_op(req_op),.req_a(req_a),.req_b(req_b),.rsp_valid(rsp_valid[0]),.rsp_ready(rsp_ready),.rsp_result(result[0]));
 custom_exec_parallel parallel(.clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(req_ready[1]),.req_op(req_op),.req_a(req_a),.req_b(req_b),.rsp_valid(rsp_valid[1]),.rsp_ready(rsp_ready),.rsp_result(result[1]));
 integer fd,count,scanned,op,cycles,passed=0;
 logic [31:0] a,b,acc,want;
 task automatic must(input logic ok,input string msg);
  if(ok!==1'b1)$fatal(1,"FAIL unit comparison %0d: %s",passed,msg);
 endtask
 initial begin
  repeat(3)@(posedge clk);@(negedge clk);rst=0;
  fd=$fopen("../verify/unit.vec","r");must(fd!=0,"open vectors");scanned=$fscanf(fd,"%d",count);
  repeat(count)begin
   scanned=$fscanf(fd,"%d %h %h %h %h",op,a,b,acc,want);must(scanned==5,"row");
   if(op>=4)continue;
   @(negedge clk);must(&req_ready,"both idle");req_op=custom_op_t'(op);req_a=a;req_b=b;req_valid=1;rsp_ready=0;
   @(posedge clk);#1;@(negedge clk);req_valid=0;req_a=~a;req_b=~b;
   cycles=0;
   while(!(&rsp_valid))begin
    @(posedge clk);#1;cycles++;
    if(cycles==1)must(rsp_valid[1] && result[1]===want,"parallel result at E1");
    must(cycles<=4,"bounded shared latency");
   end
   must(cycles==(op==0?4:1) && result[0]===want && result[1]===want,"same semantics, measured latencies");
   repeat(3)begin @(posedge clk);#1;must(&rsp_valid && result[0]===want && result[1]===want,"held responses");end
   @(negedge clk);rsp_ready=1;@(posedge clk);#1;must(&req_ready && !(|rsp_valid),"consume once");
   @(negedge clk);rsp_ready=0;passed++;
  end
  must(passed==16398,"all original vectors");
  $display("ALL 16398 SHARED/PARALLEL UNIT COMPARISONS PASSED");$finish;
 end
 initial begin #5000000;$fatal(1,"Unit comparison timeout");end
endmodule
