`timescale 1ns/1ps
module custom_exec_shared (
    input logic clk, rst,
    input logic req_valid,
    output logic req_ready,
    input fault_v_pkg::custom_op_t req_op,
    input logic [31:0] req_a, req_b,
    output logic rsp_valid,
    input logic rsp_ready,
    output logic [31:0] rsp_result
);
    import fault_v_pkg::*;
    typedef enum logic [2:0] {EU_IDLE,EU_DOT,EU_MUL,EU_ADD,EU_QNT,EU_RESPONSE} unit_state_t;
    unit_state_t state;
    logic [31:0] a_hold,b_hold;
    logic [1:0] lane;
    logic signed [17:0] accumulator,dot_sum;
    logic signed [15:0] multiply_a,multiply_b;
    logic signed [7:0] lane_a,lane_b;
    logic signed [31:0] product,shifted;
    logic signed [32:0] wide_sum;
    assign req_ready=!rst && state==EU_IDLE;
    assign rsp_valid=!rst && state==EU_RESPONSE;
    (* keep_hierarchy="yes" *) shared_mul16 u_multiplier(.a(multiply_a),.b(multiply_b),.product(product));
    always_comb begin
        lane_a=a_hold[(lane*8)+:8];
        lane_b=b_hold[(lane*8)+:8];
        multiply_a=$signed(a_hold[15:0]);
        multiply_b=$signed(b_hold[15:0]);
        if(state==EU_DOT) begin
            multiply_a={{8{lane_a[7]}},lane_a};
            multiply_b={{8{lane_b[7]}},lane_b};
        end
        dot_sum=accumulator+product;
        wide_sum=$signed({a_hold[31],a_hold})+$signed({b_hold[31],b_hold});
        shifted=$signed(a_hold) >>> b_hold[4:0];
    end
    always_ff @(posedge clk) begin
        if(rst) begin
            state<=EU_IDLE; a_hold<=0; b_hold<=0; lane<=0;
            accumulator<=0; rsp_result<=0;
        end else begin
            case(state)
                EU_IDLE: if(req_valid && req_ready) begin
                    a_hold<=req_a; b_hold<=req_b; lane<=0; accumulator<=0;
                    case(req_op)
                        CUSTOM_DOT4: state<=EU_DOT;
                        CUSTOM_MUL16: state<=EU_MUL;
                        CUSTOM_ADDSAT: state<=EU_ADD;
                        CUSTOM_QNT8: state<=EU_QNT;
                    endcase
                end
                EU_DOT: begin
                    accumulator<=dot_sum;
                    if(lane==3) begin
                        rsp_result<={{14{dot_sum[17]}},dot_sum}; state<=EU_RESPONSE;
                    end else lane<=lane+1'b1;
                end
                EU_MUL: begin rsp_result<=product; state<=EU_RESPONSE; end
                EU_ADD: begin
                    if(wide_sum>33'sd2147483647) rsp_result<=32'h7fffffff;
                    else if(wide_sum< -33'sd2147483648) rsp_result<=32'h80000000;
                    else rsp_result<=wide_sum[31:0];
                    state<=EU_RESPONSE;
                end
                EU_QNT: begin
                    if(shifted>32'sd127) rsp_result<=32'd127;
                    else if(shifted< -32'sd128) rsp_result<=32'hffffff80;
                    else rsp_result<=shifted;
                    state<=EU_RESPONSE;
                end
                EU_RESPONSE: if(rsp_valid && rsp_ready) state<=EU_IDLE;
                default: state<=EU_IDLE;
            endcase
        end
    end
endmodule

// Separate hierarchy prevents MAC extraction from cloning the multiplier.
(* keep_hierarchy="yes", use_dsp="yes" *)
module shared_mul16(
    input logic signed [15:0] a,b,
    output logic signed [31:0] product
);
    assign product=a*b;
endmodule
