`timescale 1ns/1ps
module alu (
    input logic [31:0] a, b,
    input fault_v_pkg::alu_op_t alu_op,
    output logic [31:0] result
);
    import fault_v_pkg::*;
    always_comb begin
        result=32'b0;
        case (alu_op)
            ALU_ADD: result=a+b;
            ALU_SUB: result=a-b;
            ALU_AND: result=a&b;
            ALU_OR: result=a|b;
            ALU_XOR: result=a^b;
            ALU_SLL: result=a<<b[4:0];
            ALU_SRL: result=a>>b[4:0];
            ALU_SRA: result=$signed(a)>>>b[4:0];
            ALU_SLT: result={31'b0,($signed(a)<$signed(b))};
            ALU_SLTU: result={31'b0,(a<b)};
            default: result=32'b0;
        endcase
    end
endmodule
