`timescale 1ns/1ps
module fault_v_accelerator(
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
 input logic dma_busy,
 input logic [31:0] dma_a,dma_dst,dma_count,
 output logic busy,
 output logic [31:0] src_a,src_b,dst,count
);
 import fault_v_stream_pkg::*;
 typedef enum logic [3:0] {IDLE,A_REQ,A_WAIT,B_REQ,B_WAIT,PUSH,DRAIN,WRITE_REQ,WRITE_WAIT,ABORT_WAIT} state_t;
 state_t state;
 logic done,error,start,clear;
 logic [7:0] cause,validation;
 logic [31:0] progress,fault_addr,issued,a_hold,b_hold,accumulator,bytes,dma_bytes;
 logic pipe_req_valid,pipe_req_ready,pipe_rsp_valid,pipe_rsp_ready;
 logic [31:0] pipe_result;
 logic [15:0] pipe_tag;
 wire pipe_reset=rst || !busy || state==ABORT_WAIT;
 assign busy=state!=IDLE;
 assign bytes=count<<2;assign dma_bytes=dma_count<<2;
 fault_v_job_regs #(.BASE(32'h20000400)) u_regs(.clk(clk),.rst(rst),
  .req_valid(cfg_req_valid),.req_write(cfg_req_write),.req_addr(cfg_req_addr),.req_wdata(cfg_req_wdata),.req_wstrb(cfg_req_wstrb),
  .req_ready(cfg_req_ready),.rsp_valid(cfg_rsp_valid),.rsp_err(cfg_rsp_err),.rsp_data(cfg_rsp_data),.rsp_ready(cfg_rsp_ready),
  .busy(busy),.done(done),.error(error),.cause(cause),.progress(progress),.fault_addr(fault_addr),
  .src_a(src_a),.src_b(src_b),.dst(dst),.count(count),.start(start),.clear(clear));
 fault_v_dot_pipeline u_pipe(.clk(clk),.rst(pipe_reset),.req_valid(pipe_req_valid),.req_ready(pipe_req_ready),
  .req_a(a_hold),.req_b(b_hold),.req_tag(issued[15:0]),.rsp_valid(pipe_rsp_valid),.rsp_ready(pipe_rsp_ready),
  .rsp_result(pipe_result),.rsp_tag(pipe_tag));
 always_comb begin
  validation=JOB_OK;
  if(count==0 || count>1024)validation=JOB_LENGTH;
  else if(src_a[1:0]!=0 || src_b[1:0]!=0 || dst[1:0]!=0)validation=JOB_ALIGN;
  else if(!valid_region(src_a,bytes) || !valid_region(src_b,bytes) || !valid_region(dst,4))validation=JOB_RANGE;
  else if(overlaps(dst,4,src_a,bytes) || overlaps(dst,4,src_b,bytes))validation=JOB_OVERLAP;
  else if(dma_busy && (overlaps(src_a,bytes,dma_a,dma_bytes) || overlaps(src_a,bytes,dma_dst,dma_bytes) ||
                       overlaps(src_b,bytes,dma_a,dma_bytes) || overlaps(src_b,bytes,dma_dst,dma_bytes) ||
                       overlaps(dst,4,dma_a,dma_bytes) || overlaps(dst,4,dma_dst,dma_bytes)))validation=JOB_CONFLICT;
  mem_req_valid=!rst && (state==A_REQ || state==B_REQ || state==WRITE_REQ);
  mem_req_write=state==WRITE_REQ;mem_req_wstrb=mem_req_write?4'hf:0;
  mem_req_addr=src_a+(issued<<2);
  if(state==B_REQ || state==B_WAIT)mem_req_addr=src_b+(issued<<2);
  if(state==WRITE_REQ || state==WRITE_WAIT)mem_req_addr=dst;
  mem_req_wdata=accumulator;
  mem_rsp_ready=!rst && (state==A_WAIT || state==B_WAIT || state==WRITE_WAIT || state==ABORT_WAIT);
  pipe_req_valid=!rst && state==PUSH;
  pipe_rsp_ready=!rst && busy && state!=WRITE_REQ && state!=WRITE_WAIT && state!=ABORT_WAIT;
 end
 always_ff @(posedge clk)begin
  if(rst)begin state<=IDLE;done<=0;error<=0;cause<=0;progress<=0;fault_addr<=0;issued<=0;a_hold<=0;b_hold<=0;accumulator<=0;end
  else begin
   if(clear)begin done<=0;error<=0;cause<=0;progress<=0;fault_addr<=0;end
   if(pipe_rsp_valid && pipe_rsp_ready && pipe_tag==progress[15:0])begin
    progress<=progress+1;accumulator<=accumulator+pipe_result;
    if(progress+1==count)state<=WRITE_REQ;
   end
   case(state)
    IDLE:if(start)begin
     issued<=0;progress<=0;accumulator<=0;fault_addr<=0;done<=0;error<=0;cause<=0;
     if(validation!=JOB_OK)begin done<=1;error<=1;cause<=validation;end
     else state<=A_REQ;
    end
    A_REQ:if(mem_req_valid && mem_req_ready)state<=A_WAIT;
    A_WAIT:if(mem_rsp_valid && mem_rsp_ready)begin
     if(mem_rsp_err)begin state<=IDLE;done<=1;error<=1;cause<=JOB_READ;fault_addr<=src_a+(issued<<2);end
     else begin a_hold<=mem_rsp_data;state<=B_REQ;end
    end
    B_REQ:if(mem_req_valid && mem_req_ready)state<=B_WAIT;
    B_WAIT:if(mem_rsp_valid && mem_rsp_ready)begin
     if(mem_rsp_err)begin state<=IDLE;done<=1;error<=1;cause<=JOB_READ;fault_addr<=src_b+(issued<<2);end
     else begin b_hold<=mem_rsp_data;state<=PUSH;end
    end
    PUSH:if(pipe_req_valid && pipe_req_ready)begin
     issued<=issued+1;
     if(issued+1==count)state<=DRAIN;else state<=A_REQ;
    end
    DRAIN:begin end
    WRITE_REQ:if(mem_req_valid && mem_req_ready)state<=WRITE_WAIT;
    WRITE_WAIT:if(mem_rsp_valid && mem_rsp_ready)begin
     state<=IDLE;done<=1;
     if(mem_rsp_err)begin error<=1;cause<=JOB_WRITE;fault_addr<=dst;end
    end
    ABORT_WAIT:if(mem_rsp_valid && mem_rsp_ready)begin state<=IDLE;done<=1;end
    default:state<=IDLE;
   endcase
   // Drain any accepted read before releasing the arbiter; never orphan a response.
   if(pipe_rsp_valid && pipe_rsp_ready && pipe_tag!=progress[15:0])begin
    error<=1;cause<=JOB_TAG;fault_addr<=dst;
    if((state==A_WAIT || state==B_WAIT || (mem_req_valid && mem_req_ready)) && !(mem_rsp_valid && mem_rsp_ready))begin
     state<=ABORT_WAIT;done<=0;
    end else begin state<=IDLE;done<=1;end
   end
  end
 end
endmodule
