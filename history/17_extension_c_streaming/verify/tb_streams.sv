`timescale 1ns/1ps
module tb_streams;
 import fault_v_pkg::*;
 logic clk=0;always #5 clk=~clk;
 logic [1:0] done=0;
 for(genvar g=0;g<2;g++)begin:modes
  logic rst=1;wire halted;wire [31:0] program_status;halt_cause_t halt_cause;
  fault_v_soc #(.IMEM_DELAY(g==0?1:4),.DMEM_DELAY(g==0?1:7),.UART_CLKS_PER_BIT(8)) dut(
   .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(),.uart_tx(),.program_status(program_status),.halted(halted),.halt_cause(halt_cause),
   .fault_pc(),.fault_addr(),.pc(),.state(),.retire_valid(),.retire_rd_we(),.retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
  integer id,inject,cycles,retired,concurrent_cycles,cpu_overlap,cpu_useful,tx0,tx1,tx2;logic injected;
  logic [31:0] save_addr;integer save_progress;
  task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"STREAM mode=%0d case=%0d: %s",g,id,msg);endtask
  always @(posedge clk)if(rst)begin cycles=0;retired=0;concurrent_cycles=0;cpu_overlap=0;cpu_useful=0;tx0=0;tx1=0;tx2=0;end
   else if(!done[g])begin
    cycles++;
    if(dut.u_cpu.retire_valid)begin
     retired++;if(dut.dma_busy || dut.acc_busy)begin
      cpu_overlap++;
      if(dut.u_cpu.ir==32'h00110113)cpu_useful++; // addi x2,x2,1 in unrelated CPU workload
     end
    end
    if(dut.dma_busy && dut.acc_busy)concurrent_cycles++;
    if(dut.b_req_valid && dut.b_req_ready)begin
     if(dut.m_req_ready[0])tx0++;if(dut.m_req_ready[1])tx1++;if(dut.m_req_ready[2])tx2++;
    end
    must(cycles<400000,"bounded completion");
   end
  // Inject a backend response error after the memory accepted its request.
  initial forever begin
   @(negedge clk);
   if(!rst && !injected && inject>0)begin
    if(inject<=5 && dut.b_rsp_valid && dut.b_rsp_ready &&
      ((inject==1 && dut.arb_owner==1 && dut.u_dma.state==2) ||
       (inject==2 && dut.arb_owner==1 && dut.u_dma.state==4) ||
       (inject==3 && dut.arb_owner==2 && dut.u_acc.state==2) ||
       (inject==4 && dut.arb_owner==2 && dut.u_acc.state==4) ||
       (inject==5 && dut.arb_owner==2 && dut.u_acc.state==8)))begin
     save_addr=dut.b_req_addr;save_progress=inject<=2?dut.u_dma.progress:dut.u_acc.progress;
     force dut.b_rsp_err=1;@(posedge clk);@(negedge clk);
     // XSim retains a forced variable until its continuous source changes.
     // Restore the known clean response before releasing the test-only force.
     force dut.b_rsp_err=0;@(negedge clk);release dut.b_rsp_err;injected=1;
    end
    if(inject==6 && dut.u_acc.pipe_rsp_valid && dut.u_acc.pipe_rsp_ready)begin
     force dut.u_acc.pipe_tag=16'hffff;@(posedge clk);@(negedge clk);release dut.u_acc.pipe_tag;injected=1;
    end
   end
  end
  integer fd,ef,scanned,count,hc,ds,acs,dp,ap,overlap,resettable,nchecks,region,index,runs=0,resets=0;
  logic [31:0] want;string name,stem;integer csv;
  initial begin
   inject=0;injected=0;
   csv=$fopen($sformatf("../logs/stream_mode%0d.csv",g),"w");must(csv!=0,"CSV open");
   $fdisplay(csv,"mode,id,name,repeat,cycles,retired,cpu_transactions,dma_transactions,acc_transactions,concurrent_cycles,cpu_overlap,cpu_useful");
   fd=$fopen("../verify/stream_cases.vec","r");scanned=$fscanf(fd,"%d",count);must(scanned==1 && count>100,"case manifest");
   repeat(count)begin
    scanned=$fscanf(fd,"%d %s %d %d %d %d %d %d %d %d %d",id,name,hc,ds,acs,dp,ap,inject,overlap,resettable,nchecks);must(scanned==11,"manifest row");
    stem=$sformatf("../programs/stream_%03d",id);
    for(integer rep=0;rep<3;rep++)begin
     @(negedge clk);rst=1;injected=0;
     for(integer k=0;k<4096;k++)dut.u_imem.mem[k]=0;
     $readmemh($sformatf("%s.imem",stem),dut.u_imem.mem);
     $readmemh($sformatf("%s.ram",stem),dut.u_dmem.mem);$readmemh($sformatf("%s.sp",stem),dut.u_scratch.mem);
     repeat(3)@(posedge clk);@(negedge clk);rst=0;
     if(rep==2 && resettable)begin
      wait((dut.dma_busy || dut.acc_busy) && dut.arb_pending && dut.arb_owner!=0);
      @(negedge clk);rst=1;repeat(2)@(posedge clk);#1;
      must(!dut.dma_busy && !dut.acc_busy && !dut.arb_pending && !dut.bus_pending,"reset clears active engines and arbiter");
      must(dut.dma_count==0 && dut.acc_count==0 && !dut.u_acc.pipe_rsp_valid,"reset descriptors and pipeline");
      @(negedge clk);rst=0;resets++;
     end
     wait(halted);wait(!dut.dma_busy && !dut.acc_busy);#1;
     if(halt_cause!=hc)$display("DEBUG halt=%0d want=%0d pc=%h addr=%h DMA cause=%0d progress=%0d ACC cause=%0d injected=%0d backenderr=%b ramerr=%b sperr=%b",halt_cause,hc,dut.u_cpu.fault_pc,dut.u_cpu.fault_addr,dut.u_dma.cause,dut.u_dma.progress,dut.u_acc.cause,injected,dut.b_rsp_err,dut.ram_rsp_err,dut.sp_rsp_err);
     must(halt_cause==hc,"CPU halt cause");
     if(hc==9)must(program_status==1,"normal program status");
     if(ds>=0)must({16'b0,dut.u_dma.cause,5'b0,dut.u_dma.error,dut.u_dma.done,dut.dma_busy}==ds,"DMA status");
     if(acs>=0)must({16'b0,dut.u_acc.cause,5'b0,dut.u_acc.error,dut.u_acc.done,dut.acc_busy}==acs,"ACC status");
     if(dp>=0)must(dut.u_dma.progress==dp,"DMA acknowledged progress");if(ap>=0)must(dut.u_acc.progress==ap,"ACC valid-result progress");
     if(inject)must(injected,"injection was exercised");
     if(inject==1 || inject==3)must((inject==1?dut.u_dma.fault_addr:dut.u_acc.fault_addr)==32'h10000000,"read A error address");
     if(inject==2)must(dut.u_dma.fault_addr==32'h10010000,"DMA write error address");
     if(inject==4)must(dut.u_acc.fault_addr==32'h10001000,"read B error address");
     if(inject==5 || inject==6)must(dut.u_acc.fault_addr==32'h10003000,"ACC result/tag error address");
     if(overlap)must(concurrent_cycles>0 && cpu_useful>0 && tx0>0 && tx1>0 && tx2>0,"simultaneous engines plus useful CPU progress");
     if(name.substr(4,11)=="INVALID_")must((id<96?tx1:tx2)==0,"invalid descriptor has no engine memory traffic");
     ef=$fopen($sformatf("%s.expected",stem),"r");must(ef!=0,"expected file");
     repeat(nchecks)begin
      scanned=$fscanf(ef,"%d %d %h",region,index,want);must(scanned==3,"expected row");
      if(region==0)must(dut.u_dmem.mem[index]===want,"main RAM golden result");else must(dut.u_scratch.mem[index]===want,"scratch golden result");
     end
     $fclose(ef);runs++;
     $fdisplay(csv,"%0d,%0d,%s,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",g,id,name,rep,cycles,retired,tx0,tx1,tx2,concurrent_cycles,cpu_overlap,cpu_useful);
     if(rep==0)$display("PASS STREAM mode=%0d case=%0d %s cycles=%0d",g,id,name,cycles);
    end
   end
   $fclose(fd);$fclose(csv);$display("STREAM MODE %0d COMPLETE runs=%0d resets=%0d",g,runs,resets);done[g]=1;
  end
 end
 initial begin wait(&done);$display("ALL STREAM SCENARIO RUNS PASSED; inspect per-mode run and reset totals");$finish;end
 initial begin #300000000;$fatal(1,"stream global timeout");end
endmodule
