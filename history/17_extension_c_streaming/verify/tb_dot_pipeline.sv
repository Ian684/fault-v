`timescale 1ns/1ps
module tb_dot_pipeline;
 logic clk=0;always #5 clk=~clk;
 logic rst=1,req_valid=0,rsp_ready=0;wire req_ready,rsp_valid;
 logic [31:0] req_a,req_b;logic [15:0] req_tag;wire [31:0] rsp_result;wire [15:0] rsp_tag;
 fault_v_dot_pipeline dut(.*);
 logic [31:0] av[0:16383],bv[0:16383],want[0:16383];
 integer fd,scanned,total=0,resets=0,accepted_at[0:16383];
 task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"PIPE: %s",msg);endtask
 task automatic run(input integer count,input integer random_stalls);
  integer sent,received,cycles;logic old_stall;logic [47:0] old_payload;
  sent=0;received=0;cycles=0;old_stall=0;
  while(received<count)begin
   @(negedge clk);req_valid=sent<count;req_a=av[sent%16384];req_b=bv[sent%16384];req_tag=sent;
   rsp_ready=random_stalls?($urandom_range(0,4)!=0):1;
   @(posedge clk);
   if(old_stall)must(rsp_valid && {rsp_tag,rsp_result}===old_payload,"held response stable");
   old_stall=rsp_valid && !rsp_ready;old_payload={rsp_tag,rsp_result};
   if(req_valid && req_ready)begin accepted_at[sent]=cycles;sent++;end
   if(rsp_valid && rsp_ready)begin
    must(received<sent && rsp_tag==received && rsp_result===want[received],"ordered tagged golden result");
    if(!random_stalls)must(cycles-accepted_at[received]==3,"three-clock handshake latency");
    received++;total++;
   end
   cycles++;must(cycles<count*20+100,"bounded completion");
  end
  @(negedge clk);req_valid=0;rsp_ready=1;repeat(5)@(posedge clk);#1;must(!rsp_valid,"no extra output");
  if(!random_stalls)must(cycles==count+3,"one pair per clock at full rate");
  $display("PASS PIPE count=%0d randomized=%0d cycles=%0d",count,random_stalls,cycles);
 endtask
 initial begin
  fd=$fopen("../verify/pipeline.vec","r");must(fd!=0,"vectors open");
  for(integer k=0;k<16384;k++)begin scanned=$fscanf(fd,"%h %h %h",av[k],bv[k],want[k]);must(scanned==3,"vector row");end
  $fclose(fd);repeat(3)@(posedge clk);@(negedge clk);rst=0;
  run(16384,0);run(16384,1);
  for(integer stages=0;stages<=3;stages++)begin
   @(negedge clk);rst=1;req_valid=0;rsp_ready=0;repeat(2)@(posedge clk);@(negedge clk);rst=0;
   for(integer k=0;k<stages;k++)begin req_valid=1;req_a=av[k];req_b=bv[k];req_tag=k;@(posedge clk);must(req_ready,"reset-stage acceptance");@(negedge clk);end
   req_valid=0;repeat(3)@(posedge clk);@(negedge clk);rst=1;@(posedge clk);#1;must(!rsp_valid,"reset flush output");
   @(negedge clk);rst=0;resets++;run(128,1);
  end
  $display("ALL 33280 PIPELINE RESULTS PASSED; 4 RESET FLUSHES; II=1 LATENCY=3");$finish;
 end
 initial begin #10000000;$fatal(1,"pipeline timeout");end
endmodule
