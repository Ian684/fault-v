`timescale 1ns/1ps
module tb_mem_arbiter;
 logic clk=0;always #5 clk=~clk;
 logic rst=1;logic [2:0] m_req_valid,m_req_write,m_rsp_ready;wire [2:0] m_req_ready,m_rsp_valid,m_rsp_err;
 logic [2:0][31:0] m_req_addr,m_req_wdata;wire [2:0][31:0] m_rsp_data;logic [2:0][3:0] m_req_wstrb;
 wire req_valid,req_write,rsp_ready,pending;wire [31:0] req_addr,req_wdata;wire [3:0] req_wstrb;wire [1:0] owner;
 logic req_ready=0,rsp_valid=0,rsp_err=0;logic [31:0] rsp_data=0;
 fault_v_mem_arbiter dut(.*);
 integer seqno[0:2],served[0:2],requests=0,responses=0,delay_left=0,backend_owner=0,cycles=0;
 logic [2:0] waiting=0;logic backend_busy=0,old_stall=0;logic [68:0] held;
 task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"ARBITER: %s",msg);endtask
 initial begin
  m_req_valid=0;m_req_write=0;m_rsp_ready=0;m_req_addr=0;m_req_wdata=0;m_req_wstrb=0;
  for(integer k=0;k<3;k++)begin seqno[k]=0;served[k]=0;end
  repeat(3)@(posedge clk);@(negedge clk);rst=0;
  while(responses<6000)begin
   @(negedge clk);
   for(integer k=0;k<3;k++)begin
    m_req_valid[k]=!waiting[k] && requests<6000;m_req_addr[k]=(k<<24)|seqno[k];m_req_write[k]=seqno[k]&1;
    m_req_wdata[k]=m_req_addr[k]^32'hcafebabe;m_req_wstrb[k]=m_req_write[k]?15:0;
    m_rsp_ready[k]=cycles<120?1:($urandom_range(0,3)!=0);
   end
   req_ready=!backend_busy && (cycles<120 || $urandom_range(0,3)!=0);
   if(backend_busy && delay_left>0)delay_left--;
   rsp_valid=backend_busy && delay_left==0;
   @(posedge clk);
   if(old_stall)must(req_valid && {req_write,req_addr,req_wdata,req_wstrb}===held,"request held while backend stalls");
   old_stall=req_valid && !req_ready;held={req_write,req_addr,req_wdata,req_wstrb};
   if(req_valid && req_ready)begin
    must(!backend_busy,"one backend outstanding");backend_owner=req_addr[25:24];must(m_req_ready[backend_owner],"winner ready");
    if(requests<12)must(backend_owner==requests%3,"round robin order under contention");
    waiting[backend_owner]=1;backend_busy=1;delay_left=$urandom_range(1,7);
    rsp_data=req_addr^32'h12345678;rsp_err=req_addr[0];requests++;
   end
   for(integer k=0;k<3;k++)if(m_rsp_valid[k])begin
    must(k==backend_owner && pending && owner==k,"response only to retained owner");
    must(m_rsp_data[k]===(((k<<24)|seqno[k])^32'h12345678) && m_rsp_err[k]==(seqno[k]&1),"response data and error");
    if(m_rsp_ready[k])begin waiting[k]=0;seqno[k]++;served[k]++;responses++;end
   end
   if(rsp_valid && rsp_ready)backend_busy=0;
   cycles++;must(cycles<200000,"no starvation or deadlock");
  end
  must(requests==6000 && served[0]>1900 && served[1]>1900 && served[2]>1900,"fair service counts");
  // Reset cancels an accepted pending transaction before another is granted.
  @(negedge clk);m_req_valid=3'b001;req_ready=1;rsp_valid=0;m_rsp_ready=0;
  @(posedge clk);@(negedge clk);rst=1;m_req_valid=0;@(posedge clk);#1;must(!pending && m_rsp_valid==0,"reset cancellation");
  $display("ALL 6000 ARBITER TRANSACTIONS PASSED; served=%0d,%0d,%0d; RESET CANCEL PASSED",served[0],served[1],served[2]);$finish;
 end
endmodule
