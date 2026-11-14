`timescale 1ns/1ps
module custom_exec(
 input logic clk,rst,req_valid,
 output logic req_ready,
 input fault_v_pkg::custom_op_t req_op,
 input logic [31:0] req_a,req_b,req_acc,
 output logic rsp_valid,
 input logic rsp_ready,
 output logic [31:0] rsp_result
);
 import fault_v_pkg::*;
 typedef enum logic [2:0] {EU_IDLE,EU_EXEC,EU_DOT8_SECOND,EU_REQUANT,EU_RESPONSE} unit_state_t;
 unit_state_t state;
 custom_op_t op_hold;
 logic [31:0] a_hold,b_hold,acc_hold;
 logic signed [15:0] mul_a[0:3],mul_b[0:3];
 wire signed [31:0] product[0:3];
 logic signed [7:0] lane_a[0:3],lane_b[0:3];
 logic signed [3:0] nib_a[0:3],nib_b[0:3];
 logic signed [8:0] byte_sum[0:3];
 logic [31:0] packed_sat;
 logic signed [17:0] dot_sum,partial_dot;
 logic signed [32:0] pair_sum,wide_sum;
 logic signed [31:0] shifted;
 logic signed [47:0] scaled_next,scaled_hold,low_term,high_term,correction;
 logic [48:0] magnitude,rounded_magnitude,round_bias;
 logic signed [48:0] rounded_value,requant_value;
 logic signed [7:0] zero_point;
 logic [4:0] shift_count;
 integer lane_base;
 assign req_ready=!rst && state==EU_IDLE;
 assign rsp_valid=!rst && state==EU_RESPONSE;
 for(genvar k=0;k<4;k++)begin: multipliers
  fault_v_mul16 u_multiplier(.a(mul_a[k]),.b(mul_b[k]),.product(product[k]));
 end
 always_comb begin
  lane_base=(state==EU_DOT8_SECOND)?4:0;packed_sat=0;
  for(integer k=0;k<4;k++)begin
   lane_a[k]=$signed(a_hold[k*8+:8]);lane_b[k]=$signed(b_hold[k*8+:8]);
   nib_a[k]=$signed(a_hold[(k+lane_base)*4+:4]);nib_b[k]=$signed(b_hold[(k+lane_base)*4+:4]);
   mul_a[k]={{8{lane_a[k][7]}},lane_a[k]};mul_b[k]={{8{lane_b[k][7]}},lane_b[k]};
   if(op_hold==CUSTOM_DOT4SU)mul_b[k]={8'b0,b_hold[k*8+:8]};
   if(op_hold==CUSTOM_DOT8)begin
    mul_a[k]={{12{nib_a[k][3]}},nib_a[k]};mul_b[k]={{12{nib_b[k][3]}},nib_b[k]};
   end
   if(op_hold==CUSTOM_SUB8SAT)
    byte_sum[k]=$signed({lane_a[k][7],lane_a[k]})-$signed({lane_b[k][7],lane_b[k]});
   else byte_sum[k]=$signed({lane_a[k][7],lane_a[k]})+$signed({lane_b[k][7],lane_b[k]});
   if(byte_sum[k]>9'sd127)packed_sat[k*8+:8]=8'h7f;
   else if(byte_sum[k]< -9'sd128)packed_sat[k*8+:8]=8'h80;
   else packed_sat[k*8+:8]=byte_sum[k][7:0];
  end
  if(op_hold inside {CUSTOM_MUL16,CUSTOM_MAC16,CUSTOM_DOT2SAT,CUSTOM_RQNT8})begin
   mul_a[0]=$signed(a_hold[15:0]);mul_b[0]=$signed(b_hold[15:0]);
   mul_a[1]=$signed(a_hold[31:16]);
   mul_b[1]=(op_hold==CUSTOM_RQNT8)?$signed(b_hold[15:0]):$signed(b_hold[31:16]);
  end
  // Each INT8/INT4 product fits 18 bits; the 18-bit sum cannot overflow.
  dot_sum=$signed(product[0][17:0])+$signed(product[1][17:0])+$signed(product[2][17:0])+$signed(product[3][17:0]);
  pair_sum=$signed({product[0][31],product[0]})+$signed({product[1][31],product[1]});
  wide_sum=$signed({a_hold[31],a_hold})+$signed({b_hold[31],b_hold});
  shifted=$signed(a_hold) >>> b_hold[4:0];
  // Exact INT32*INT16 from signed low/high 16-bit products plus low sign correction.
  low_term={{16{product[0][31]}},product[0]};high_term={product[1],16'b0};
  correction=a_hold[15]?{{16{b_hold[15]}},b_hold[15:0],16'b0}:48'sd0;
  scaled_next=low_term+high_term+correction;
  shift_count=b_hold[20:16];zero_point=$signed(b_hold[28:21]);
  magnitude=scaled_hold[47]?-$signed({scaled_hold[47],scaled_hold}):{1'b0,scaled_hold};
  round_bias=49'd0;
  if(shift_count!=0)round_bias=49'd1 << (shift_count-1'b1);
  rounded_magnitude=(magnitude+round_bias) >> shift_count;
  rounded_value=scaled_hold[47]?-$signed(rounded_magnitude):$signed(rounded_magnitude);
  requant_value=rounded_value+$signed({{41{zero_point[7]}},zero_point});
 end
 always_ff @(posedge clk)begin
  if(rst)begin
   state<=EU_IDLE;op_hold<=CUSTOM_DOT4;a_hold<=0;b_hold<=0;acc_hold<=0;
   partial_dot<=0;scaled_hold<=0;rsp_result<=0;
  end else case(state)
   EU_IDLE:if(req_valid && req_ready)begin
    a_hold<=req_a;b_hold<=req_b;acc_hold<=req_acc;op_hold<=req_op;
    partial_dot<=0;state<=EU_EXEC;
   end
   EU_EXEC:begin
    state<=EU_RESPONSE;
    case(op_hold)
     CUSTOM_DOT4,CUSTOM_DOT4SU:rsp_result<={{14{dot_sum[17]}},dot_sum};
     CUSTOM_DOT4ACC:rsp_result<=acc_hold+{{14{dot_sum[17]}},dot_sum};
     CUSTOM_MUL16:rsp_result<=product[0];
     CUSTOM_MAC16:rsp_result<=acc_hold+product[0];
     CUSTOM_ADDSAT:begin
      if(wide_sum>33'sd2147483647)rsp_result<=32'h7fffffff;
      else if(wide_sum< -33'sd2147483648)rsp_result<=32'h80000000;
      else rsp_result<=wide_sum[31:0];
     end
     CUSTOM_QNT8:begin
      if(shifted>32'sd127)rsp_result<=32'd127;
      else if(shifted< -32'sd128)rsp_result<=32'hffffff80;
      else rsp_result<=shifted;
     end
     CUSTOM_ADD8SAT,CUSTOM_SUB8SAT:rsp_result<=packed_sat;
     CUSTOM_DOT2SAT:begin
      if(pair_sum>33'sd2147483647)rsp_result<=32'h7fffffff;
      else if(pair_sum< -33'sd2147483648)rsp_result<=32'h80000000;
      else rsp_result<=pair_sum[31:0];
     end
     CUSTOM_DOT8:begin partial_dot<=dot_sum;state<=EU_DOT8_SECOND;end
     CUSTOM_RQNT8:begin scaled_hold<=scaled_next;state<=EU_REQUANT;end
     default:rsp_result<=0;
    endcase
   end
   EU_DOT8_SECOND:begin
    rsp_result<={{14{partial_dot[17]}},partial_dot}+{{14{dot_sum[17]}},dot_sum};state<=EU_RESPONSE;
   end
   EU_REQUANT:begin
    if(requant_value>49'sd127)rsp_result<=32'd127;
    else if(requant_value< -49'sd128)rsp_result<=32'hffffff80;
    else rsp_result<=requant_value[31:0];
    state<=EU_RESPONSE;
   end
   EU_RESPONSE:if(rsp_valid && rsp_ready)state<=EU_IDLE;
   default:state<=EU_IDLE;
  endcase
 end
endmodule
module fault_v_mul16(input logic signed [15:0] a,b,output logic signed [31:0] product);
 assign product=a*b;
endmodule
