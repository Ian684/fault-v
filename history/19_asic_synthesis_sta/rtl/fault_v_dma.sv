`timescale 1ns/1ps
module fault_v_dma(
 input logic clk,rst,cfg_req_valid,cfg_req_write,
 input logic [31:0] cfg_req_addr,cfg_req_wdata,
 input logic [3:0] cfg_req_wstrb,
 output logic cfg_req_ready,cfg_rsp_valid,cfg_rsp_err,
 output logic [31:0] cfg_rsp_data,
 input logic cfg_rsp_ready,
 output logic mem_req_valid,mem_req_write,
 output logic [31:0] mem_req_addr,mem_req_wdata,
 output logic [3:0] mem_req_wstrb,
 input logic mem_req_ready,mem_rsp_valid,mem_rsp_err,
 input logic [31:0] mem_rsp_data,
 output logic mem_rsp_ready,
 input logic acc_busy,
 input logic [31:0] acc_a,acc_b,acc_dst,acc_count,
 output logic busy,
 output logic [31:0] src_a,src_b,dst,count
);
 import fault_v_stream_pkg::*;
 typedef enum logic [2:0] {IDLE,READ_REQ,READ_WAIT,WRITE_REQ,WRITE_WAIT} state_t;
 state_t state;
 logic done,error,start,clear;
 logic [7:0] cause,validation;
 logic [31:0] progress,fault_addr,buffer_word,bytes,acc_bytes;
 assign busy=state!=IDLE;
 assign bytes=count<<2;assign acc_bytes=acc_count<<2;
 fault_v_job_regs #(.BASE(32'h20000300)) u_regs(.clk(clk),.rst(rst),
  .req_valid(cfg_req_valid),.req_write(cfg_req_write),.req_addr(cfg_req_addr),.req_wdata(cfg_req_wdata),.req_wstrb(cfg_req_wstrb),
  .req_ready(cfg_req_ready),.rsp_valid(cfg_rsp_valid),.rsp_err(cfg_rsp_err),.rsp_data(cfg_rsp_data),.rsp_ready(cfg_rsp_ready),
  .busy(busy),.done(done),.error(error),.cause(cause),.progress(progress),.fault_addr(fault_addr),
  .src_a(src_a),.src_b(src_b),.dst(dst),.count(count),.start(start),.clear(clear));
 always_comb begin
  validation=JOB_OK;
  if(count==0 || count>1024)validation=JOB_LENGTH;
  else if(src_a[1:0]!=0 || dst[1:0]!=0)validation=JOB_ALIGN;
  else if(!valid_region(src_a,bytes) || !valid_region(dst,bytes))validation=JOB_RANGE;
  else if(overlaps(src_a,bytes,dst,bytes))validation=JOB_OVERLAP;
  else if(acc_busy && (overlaps(src_a,bytes,acc_a,acc_bytes) || overlaps(src_a,bytes,acc_b,acc_bytes) || overlaps(src_a,bytes,acc_dst,4) ||
                       overlaps(dst,bytes,acc_a,acc_bytes) || overlaps(dst,bytes,acc_b,acc_bytes) || overlaps(dst,bytes,acc_dst,4)))validation=JOB_CONFLICT;
  mem_req_valid=!rst && (state==READ_REQ || state==WRITE_REQ);
  mem_req_write=state==WRITE_REQ;
  mem_req_addr=(state==WRITE_REQ || state==WRITE_WAIT)?dst+(progress<<2):src_a+(progress<<2);
  mem_req_wdata=buffer_word;mem_req_wstrb=mem_req_write?4'hf:0;
  mem_rsp_ready=!rst && (state==READ_WAIT || state==WRITE_WAIT);
 end
 always_ff @(posedge clk)begin
  if(rst)begin state<=IDLE;done<=0;error<=0;cause<=0;progress<=0;fault_addr<=0;buffer_word<=0;end
  else begin
   if(clear)begin done<=0;error<=0;cause<=0;progress<=0;fault_addr<=0;end
   case(state)
    IDLE:if(start)begin
     progress<=0;fault_addr<=0;done<=0;error<=0;cause<=0;
     if(validation!=JOB_OK)begin done<=1;error<=1;cause<=validation;end
     else state<=READ_REQ;
    end
    READ_REQ:if(mem_req_valid && mem_req_ready)state<=READ_WAIT;
    READ_WAIT:if(mem_rsp_valid && mem_rsp_ready)begin
     if(mem_rsp_err)begin state<=IDLE;done<=1;error<=1;cause<=JOB_READ;fault_addr<=src_a+(progress<<2);end
     else begin buffer_word<=mem_rsp_data;state<=WRITE_REQ;end
    end
    WRITE_REQ:if(mem_req_valid && mem_req_ready)state<=WRITE_WAIT;
    WRITE_WAIT:if(mem_rsp_valid && mem_rsp_ready)begin
     if(mem_rsp_err)begin state<=IDLE;done<=1;error<=1;cause<=JOB_WRITE;fault_addr<=dst+(progress<<2);end
     else begin
      progress<=progress+1;
      if(progress+1==count)begin state<=IDLE;done<=1;end
      else state<=READ_REQ;
     end
    end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
