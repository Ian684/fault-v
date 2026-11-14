`timescale 1ns/1ps
module custom_exec_parallel(
 input logic clk,rst,req_valid,
 output logic req_ready,
 input fault_v_pkg::custom_op_t req_op,
 input logic [31:0] req_a,req_b,
 output logic rsp_valid,
 input logic rsp_ready,
 output logic [31:0] rsp_result
);
 import fault_v_pkg::*;
 typedef enum logic [1:0] {IDLE,EXEC,RESP} state_t;
 state_t state;custom_op_t op;
 logic [31:0] a,b;
 wire signed [31:0] product[0:3];
 logic signed [15:0] ma[0:3],mb[0:3];
 logic signed [17:0] dot;
 logic signed [32:0] sum;
 logic signed [31:0] shifted;
 assign req_ready=!rst && state==IDLE;
 assign rsp_valid=!rst && state==RESP;
 for(genvar k=0;k<4;k++)begin: lanes
  (* keep_hierarchy="yes" *) parallel_mul16 u_mul(.a(ma[k]),.b(mb[k]),.product(product[k]));
 end
 always_comb begin
  for(integer k=0;k<4;k++)begin
   ma[k]={{8{a[k*8+7]}},a[k*8+:8]};mb[k]={{8{b[k*8+7]}},b[k*8+:8]};
  end
  if(op==CUSTOM_MUL16)begin ma[0]=$signed(a[15:0]);mb[0]=$signed(b[15:0]);end
  dot=$signed(product[0][17:0])+$signed(product[1][17:0])+$signed(product[2][17:0])+$signed(product[3][17:0]);
  sum=$signed({a[31],a})+$signed({b[31],b});shifted=$signed(a) >>> b[4:0];
 end
 always_ff @(posedge clk)begin
  if(rst)begin state<=IDLE;op<=CUSTOM_DOT4;a<=0;b<=0;rsp_result<=0;end
  else case(state)
   IDLE:if(req_valid && req_ready)begin op<=req_op;a<=req_a;b<=req_b;state<=EXEC;end
   EXEC:begin
    case(op)
     CUSTOM_DOT4:rsp_result<={{14{dot[17]}},dot};
     CUSTOM_MUL16:rsp_result<=product[0];
     CUSTOM_ADDSAT:if(sum>33'sd2147483647)rsp_result<=32'h7fffffff;else if(sum< -33'sd2147483648)rsp_result<=32'h80000000;else rsp_result<=sum[31:0];
     CUSTOM_QNT8:if(shifted>32'sd127)rsp_result<=127;else if(shifted< -32'sd128)rsp_result<=32'hffffff80;else rsp_result<=shifted;
     default:rsp_result<=0;
    endcase
    state<=RESP;
   end
   RESP:if(rsp_valid && rsp_ready)state<=IDLE;
   default:state<=IDLE;
  endcase
 end
endmodule
(* keep_hierarchy="yes", use_dsp="yes" *)
module parallel_mul16(input logic signed [15:0] a,b,output logic signed [31:0] product);
 assign product=a*b;
endmodule
