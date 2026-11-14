`timescale 1ns/1ps
module branch_compare (
    input logic [31:0] a,b,
    input fault_v_pkg::branch_op_t branch_op,
    output logic taken
);
    import fault_v_pkg::*;
    always_comb begin
        taken=1'b0;
        case (branch_op)
            BR_EQ: taken=(a==b);
            BR_NE: taken=(a!=b);
            BR_LT: taken=($signed(a)<$signed(b));
            BR_GE: taken=($signed(a)>=$signed(b));
            BR_LTU: taken=(a<b);
            BR_GEU: taken=(a>=b);
            default: taken=1'b0;
        endcase
    end
endmodule
