`timescale 1ns/1ps
module fault_v_mem_arbiter(
 input logic clk,rst,
 input logic [2:0] m_req_valid,m_req_write,
 input logic [2:0][31:0] m_req_addr,m_req_wdata,
 input logic [2:0][3:0] m_req_wstrb,
 output logic [2:0] m_req_ready,m_rsp_valid,m_rsp_err,
 output logic [2:0][31:0] m_rsp_data,
 input logic [2:0] m_rsp_ready,
 output logic req_valid,req_write,
 output logic [31:0] req_addr,req_wdata,
 output logic [3:0] req_wstrb,
 input logic req_ready,rsp_valid,rsp_err,
 input logic [31:0] rsp_data,
 output logic rsp_ready,
 output logic pending,
 output logic [1:0] owner
);
 logic [1:0] round_robin,grant,held_grant;
 logic hold_grant,found;
 integer candidate;
 always_comb begin
  grant=0;found=0;candidate=0;
  if(hold_grant)begin grant=held_grant;found=1;end
  else for(integer k=0;k<3;k++)begin
   candidate=(int'(round_robin)+k)%3;
   if(!found && m_req_valid[candidate])begin grant=candidate[1:0];found=1;end
  end
  req_valid=!rst && !pending && found && m_req_valid[grant];
  req_write=m_req_write[grant];req_addr=m_req_addr[grant];req_wdata=m_req_wdata[grant];req_wstrb=m_req_wstrb[grant];
  m_req_ready=0;m_rsp_valid=0;m_rsp_err=0;m_rsp_data=0;rsp_ready=0;
  if(!rst)begin
   if(!pending && found)m_req_ready[grant]=req_ready;
   if(pending)begin
    m_rsp_valid[owner]=rsp_valid;m_rsp_err[owner]=rsp_err;m_rsp_data[owner]=rsp_data;
    rsp_ready=m_rsp_ready[owner];
   end
  end
 end
 always_ff @(posedge clk)begin
  if(rst)begin pending<=0;owner<=0;round_robin<=0;hold_grant<=0;held_grant<=0;end
  else begin
   if(req_valid && !req_ready)begin hold_grant<=1;held_grant<=grant;end
   if(req_valid && req_ready)begin pending<=1;owner<=grant;hold_grant<=0;end
   if(pending && rsp_valid && rsp_ready)begin pending<=0;round_robin<=(owner==2)?0:owner+1'b1;end
  end
 end
endmodule
