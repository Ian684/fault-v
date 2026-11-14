`timescale 1ns/1ps
module fault_v_job_regs #(parameter logic [31:0] BASE=32'h20000300)(
 input logic clk,rst,req_valid,req_write,
 input logic [31:0] req_addr,req_wdata,
 input logic [3:0] req_wstrb,
 output logic req_ready,rsp_valid,rsp_err,
 output logic [31:0] rsp_data,
 input logic rsp_ready,busy,done,error,
 input logic [7:0] cause,
 input logic [31:0] progress,fault_addr,
 output logic [31:0] src_a,src_b,dst,count,
 output logic start,clear
);
 wire fire=req_valid && req_ready;
 wire address_ok=req_addr[31:5]==BASE[31:5] && req_addr[1:0]==0;
 wire control_write=fire && address_ok && req_write && req_wstrb==4'hf && req_addr[4:2]==0 && !busy;
 assign start=!rst && control_write && req_wdata==1;
 assign clear=!rst && control_write && req_wdata==2;
 assign req_ready=!rst && !rsp_valid;
 always_ff @(posedge clk)begin
  if(rst)begin src_a<=0;src_b<=0;dst<=0;count<=0;rsp_valid<=0;rsp_err<=0;rsp_data<=0;end
  else begin
   if(rsp_valid && rsp_ready)rsp_valid<=0;
   if(fire)begin
    rsp_valid<=1;rsp_err<=0;rsp_data<=0;
    if(!address_ok || (req_write && req_wstrb!=4'hf))rsp_err<=1;
    else if(req_write)begin
     if(busy)rsp_err<=1;
     else case(req_addr[4:2])
      0:if(req_wdata>2)rsp_err<=1;
      2:src_a<=req_wdata;
      3:src_b<=req_wdata;
      4:dst<=req_wdata;
      5:count<=req_wdata;
      default:rsp_err<=1;
     endcase
    end else case(req_addr[4:2])
     0:rsp_data<=0;
     1:rsp_data<={16'b0,cause,5'b0,error,done,busy};
     2:rsp_data<=src_a;
     3:rsp_data<=src_b;
     4:rsp_data<=dst;
     5:rsp_data<=count;
     6:rsp_data<=progress;
     7:rsp_data<=fault_addr;
    endcase
   end
  end
 end
endmodule
