`timescale 1ns/1ps
package fault_v_pkg;
    typedef enum logic [3:0] {
        ALU_ADD=4'd0, ALU_SUB=4'd1, ALU_AND=4'd2, ALU_OR=4'd3,
        ALU_XOR=4'd4, ALU_SLL=4'd5, ALU_SRL=4'd6, ALU_SRA=4'd7,
        ALU_SLT=4'd8, ALU_SLTU=4'd9
    } alu_op_t;
    typedef enum logic [2:0] {
        IMM_NONE=3'd0, IMM_I=3'd1, IMM_S=3'd2,
        IMM_B=3'd3, IMM_U=3'd4, IMM_J=3'd5
    } imm_sel_t;
    typedef enum logic [3:0] {
        IC_INVALID=4'd0, IC_ALU=4'd1, IC_LOAD=4'd2, IC_STORE=4'd3,
        IC_BRANCH=4'd4, IC_JAL=4'd5, IC_JALR=4'd6,
        IC_FENCE=4'd7, IC_ECALL=4'd8, IC_EBREAK=4'd9
    } instr_class_t;
    typedef enum logic [1:0] {
        ALU_A_REG=2'd0, ALU_A_PC=2'd1, ALU_A_ZERO=2'd2
    } alu_src_a_t;
    typedef enum logic { ALU_B_REG=1'b0, ALU_B_IMM=1'b1 } alu_src_b_t;
    typedef enum logic [2:0] {
        BR_NONE=3'd0, BR_EQ=3'd1, BR_NE=3'd2, BR_LT=3'd3,
        BR_GE=3'd4, BR_LTU=3'd5, BR_GEU=3'd6
    } branch_op_t;
    typedef enum logic [1:0] {
        MEM_BYTE=2'd0, MEM_HALF=2'd1, MEM_WORD=2'd2
    } mem_size_t;
    typedef enum logic [1:0] {
        WB_ALU=2'd0, WB_LOAD=2'd1, WB_PC4=2'd2
    } wb_sel_t;
    typedef enum logic [3:0] {
        ST_FETCH=4'd0, ST_DECODE=4'd1, ST_ALU_EXEC=4'd2,
        ST_ALU_WB=4'd3, ST_ADDR_EXEC=4'd4, ST_MEM_CHECK=4'd5,
        ST_LOAD_WAIT=4'd6, ST_LOAD_WB=4'd7, ST_STORE_WAIT=4'd8,
        ST_BR_EXEC=4'd9, ST_BR_COMMIT=4'd10, ST_JUMP_EXEC=4'd11,
        ST_JUMP_COMMIT=4'd12, ST_FENCE_COMMIT=4'd13, ST_HALTED=4'd14
    } cpu_state_t;
    typedef enum logic { PC_SEQ=1'b0, PC_TARGET=1'b1 } pc_sel_t;
    typedef enum logic [3:0] {
        HALT_NONE=4'd0, HALT_ILLEGAL=4'd1, HALT_INSTR_ALIGN=4'd2,
        HALT_FETCH_ACCESS=4'd3, HALT_LOAD_ALIGN=4'd4, HALT_STORE_ALIGN=4'd5,
        HALT_LOAD_ACCESS=4'd6, HALT_STORE_ACCESS=4'd7,
        HALT_ECALL=4'd8, HALT_EBREAK=4'd9, HALT_INTERNAL=4'd10
    } halt_cause_t;
endpackage
