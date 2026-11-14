`timescale 1ns/1ps
module decoder (
    input logic [31:0] instruction,
    output logic [4:0] rs1_addr, rs2_addr, rd_addr,
    output fault_v_pkg::instr_class_t instr_class,
    output fault_v_pkg::alu_op_t alu_op,
    output fault_v_pkg::imm_sel_t imm_sel,
    output fault_v_pkg::alu_src_a_t alu_src_a,
    output fault_v_pkg::alu_src_b_t alu_src_b,
    output fault_v_pkg::branch_op_t branch_op,
    output fault_v_pkg::mem_size_t mem_size,
    output logic load_unsigned, rd_write,
    output fault_v_pkg::wb_sel_t wb_sel,
    output fault_v_pkg::custom_op_t custom_op,
    output logic illegal
);
    import fault_v_pkg::*;
    logic [6:0] opcode, funct7;
    logic [2:0] funct3;
    assign opcode = instruction[6:0];
    assign funct3 = instruction[14:12];
    assign funct7 = instruction[31:25];
    assign rs1_addr = instruction[19:15];
    assign rs2_addr = instruction[24:20];
    assign rd_addr = instruction[11:7];

    always_comb begin
        instr_class = IC_INVALID;
        alu_op = ALU_ADD;
        imm_sel = IMM_NONE;
        alu_src_a = ALU_A_ZERO;
        alu_src_b = ALU_B_IMM;
        branch_op = BR_NONE;
        mem_size = MEM_WORD;
        load_unsigned = 1'b0;
        rd_write = 1'b0;
        wb_sel = WB_ALU;
        illegal = 1'b1;
        custom_op = CUSTOM_DOT4;

        case (opcode)
            7'h0b: begin
                if (funct7 == 0 && funct3 <= 3) begin
                    instr_class = IC_CUSTOM;
                    custom_op = custom_op_t'(funct3[1:0]);
                    rd_write = 1'b1;
                    wb_sel = WB_CUSTOM;
                    illegal = 1'b0;
                end
            end
            7'h33: begin // Register-register integer operations
                instr_class = IC_ALU;
                alu_src_a = ALU_A_REG;
                alu_src_b = ALU_B_REG;
                rd_write = 1'b1;
                case ({funct7, funct3})
                    10'b0000000_000: begin alu_op=ALU_ADD;  illegal=0; end
                    10'b0100000_000: begin alu_op=ALU_SUB;  illegal=0; end
                    10'b0000000_001: begin alu_op=ALU_SLL;  illegal=0; end
                    10'b0000000_010: begin alu_op=ALU_SLT;  illegal=0; end
                    10'b0000000_011: begin alu_op=ALU_SLTU; illegal=0; end
                    10'b0000000_100: begin alu_op=ALU_XOR;  illegal=0; end
                    10'b0000000_101: begin alu_op=ALU_SRL;  illegal=0; end
                    10'b0100000_101: begin alu_op=ALU_SRA;  illegal=0; end
                    10'b0000000_110: begin alu_op=ALU_OR;   illegal=0; end
                    10'b0000000_111: begin alu_op=ALU_AND;  illegal=0; end
                    default: begin end
                endcase
            end
            7'h13: begin // Register-immediate integer operations
                instr_class = IC_ALU;
                alu_src_a = ALU_A_REG;
                imm_sel = IMM_I;
                rd_write = 1'b1;
                case (funct3)
                    3'b000: begin alu_op=ALU_ADD;  illegal=0; end
                    3'b010: begin alu_op=ALU_SLT;  illegal=0; end
                    3'b011: begin alu_op=ALU_SLTU; illegal=0; end
                    3'b100: begin alu_op=ALU_XOR;  illegal=0; end
                    3'b110: begin alu_op=ALU_OR;   illegal=0; end
                    3'b111: begin alu_op=ALU_AND;  illegal=0; end
                    3'b001: begin
                        if (funct7 == 7'h00) begin alu_op=ALU_SLL; illegal=0; end
                    end
                    3'b101: begin
                        if (funct7 == 7'h00) begin alu_op=ALU_SRL; illegal=0; end
                        else if (funct7 == 7'h20) begin alu_op=ALU_SRA; illegal=0; end
                    end
                    default: begin end
                endcase
            end
            7'h37: begin // LUI
                instr_class=IC_ALU; imm_sel=IMM_U;
                rd_write=1; illegal=0;
            end
            7'h17: begin // AUIPC
                instr_class=IC_ALU; imm_sel=IMM_U; alu_src_a=ALU_A_PC;
                rd_write=1; illegal=0;
            end
            7'h63: begin // Conditional branches
                instr_class=IC_BRANCH; imm_sel=IMM_B; alu_src_a=ALU_A_PC;
                case (funct3)
                    3'b000: begin branch_op=BR_EQ;  illegal=0; end
                    3'b001: begin branch_op=BR_NE;  illegal=0; end
                    3'b100: begin branch_op=BR_LT;  illegal=0; end
                    3'b101: begin branch_op=BR_GE;  illegal=0; end
                    3'b110: begin branch_op=BR_LTU; illegal=0; end
                    3'b111: begin branch_op=BR_GEU; illegal=0; end
                    default: begin end
                endcase
            end
            7'h6f: begin // JAL
                instr_class=IC_JAL; imm_sel=IMM_J; alu_src_a=ALU_A_PC;
                rd_write=1; wb_sel=WB_PC4; illegal=0;
            end
            7'h67: begin // JALR
                if (funct3 == 3'b000) begin
                    instr_class=IC_JALR; imm_sel=IMM_I; alu_src_a=ALU_A_REG;
                    rd_write=1; wb_sel=WB_PC4; illegal=0;
                end
            end
            7'h03: begin // Loads
                instr_class=IC_LOAD; imm_sel=IMM_I; alu_src_a=ALU_A_REG;
                rd_write=1; wb_sel=WB_LOAD;
                case (funct3)
                    3'b000: begin mem_size=MEM_BYTE; illegal=0; end
                    3'b001: begin mem_size=MEM_HALF; illegal=0; end
                    3'b010: begin mem_size=MEM_WORD; illegal=0; end
                    3'b100: begin mem_size=MEM_BYTE; load_unsigned=1; illegal=0; end
                    3'b101: begin mem_size=MEM_HALF; load_unsigned=1; illegal=0; end
                    default: begin end
                endcase
            end
            7'h23: begin // Stores
                instr_class=IC_STORE; imm_sel=IMM_S; alu_src_a=ALU_A_REG;
                case (funct3)
                    3'b000: begin mem_size=MEM_BYTE; illegal=0; end
                    3'b001: begin mem_size=MEM_HALF; illegal=0; end
                    3'b010: begin mem_size=MEM_WORD; illegal=0; end
                    default: begin end
                endcase
            end
            7'h0f: begin
                // Conservative FENCE: ignore fm, pred, succ, rs1 and rd.
                // FENCE.I (funct3=001) is not implemented.
                if (funct3 == 3'b000) begin instr_class=IC_FENCE; illegal=0; end
            end
            7'h73: begin
                // Exact encodings: do not accept malformed SYSTEM instructions.
                if (instruction == 32'h00000073) begin
                    instr_class=IC_ECALL; illegal=0;
                end else if (instruction == 32'h00100073) begin
                    instr_class=IC_EBREAK; illegal=0;
                end
            end
            default: begin end
        endcase

        // Remove all partially decoded controls on an illegal instruction.
        if (illegal) begin
            instr_class=IC_INVALID; alu_op=ALU_ADD; imm_sel=IMM_NONE;
            alu_src_a=ALU_A_ZERO; alu_src_b=ALU_B_IMM; branch_op=BR_NONE;
            mem_size=MEM_WORD; load_unsigned=0; rd_write=0; wb_sel=WB_ALU;
        end
    end
endmodule
