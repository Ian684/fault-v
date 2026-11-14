`timescale 1ns/1ps
module fault_v_dot_pipeline(
 input logic clk,rst,req_valid,
 output logic req_ready,
 input logic [31:0] req_a,req_b,
 input logic [15:0] req_tag,
 output logic rsp_valid,
 input logic rsp_ready,
 output logic [31:0] rsp_result,
 output logic [15:0] rsp_tag
);
 logic v1,v2,v3;
 wire r3=!v3 || rsp_ready;
 wire r2=!v2 || r3;
 wire r1=!v1 || r2;
 logic signed [15:0] p1[0:3];
 logic signed [16:0] pair0,pair1;
 logic [15:0] tag1,tag2;
 logic signed [17:0] total;
 wire signed [31:0] product[0:3];
 for(genvar k=0;k<4;k++)begin: multipliers
  wire signed [15:0] a={{8{req_a[k*8+7]}},req_a[k*8+:8]};
  wire signed [15:0] b={{8{req_b[k*8+7]}},req_b[k*8+:8]};
  fault_v_mul16 u_multiplier(.a(a),.b(b),.product(product[k]));
 end
 assign total=$signed({pair0[16],pair0})+$signed({pair1[16],pair1});
 assign req_ready=!rst && r1;
 assign rsp_valid=!rst && v3;
 always_ff @(posedge clk)begin
  if(rst)begin
   v1<=0;v2<=0;v3<=0;tag1<=0;tag2<=0;rsp_tag<=0;pair0<=0;pair1<=0;rsp_result<=0;
   for(integer k=0;k<4;k++)p1[k]<=0;
  end else begin
   if(r3)begin
    v3<=v2;
    if(v2)begin rsp_result<={{14{total[17]}},total};rsp_tag<=tag2;end
   end
   if(r2)begin
    v2<=v1;
    if(v1)begin
     pair0<=$signed({p1[0][15],p1[0]})+$signed({p1[1][15],p1[1]});
     pair1<=$signed({p1[2][15],p1[2]})+$signed({p1[3][15],p1[3]});tag2<=tag1;
    end
   end
   if(r1)begin
    v1<=req_valid;
    if(req_valid)begin
     for(integer k=0;k<4;k++)p1[k]<=product[k][15:0];
     tag1<=req_tag;
    end
   end
  end
 end
endmodule
