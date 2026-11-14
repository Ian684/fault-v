`timescale 1ns/1ps
module pc_path (
    input  logic        clk,
    input  logic        rst,

    input  logic        exec_we,
    input  logic        commit_en,

    input  logic [31:0] instr_pc,
    input  logic [31:0] rs1_value,
    input  logic [31:0] imm,
    input  logic        is_jalr,
    input  logic        take_target,

    output logic [31:0] target_pc,
    output logic [31:0] pc_next,
    output logic        target_misaligned,
    output logic [31:0] pc
);

    import fault_v_pkg::*;

    logic [31:0] alu_a;
    logic [31:0] alu_result;
    logic [31:0] target_value;

    logic [31:0] sequential_pc;
    logic        take_target_q;
    logic        pc_we;

    // Branch/JAL 使用 InstrPC；JALR 使用 rs1
    assign alu_a = is_jalr ? rs1_value : instr_pc;

    // 使用既有 ALU
    alu u_alu (
        .a      (alu_a),
        .b      (imm),
        .alu_op (ALU_ADD),
        .result (alu_result)
    );

    // JALR 先清除最低位，再保存目標
    assign target_value =
        is_jalr
        ? (alu_result & 32'hFFFFFFFE)
        : alu_result;

    // Execute：保存目標、順序位址與選擇
    always_ff @(posedge clk) begin
        if (rst) begin
            target_pc     <= 32'b0;
            sequential_pc <= 32'b0;
            take_target_q <= 1'b0;
        end
        else if (exec_we) begin
            target_pc     <= target_value;
            sequential_pc <= instr_pc + 32'd4;
            take_target_q <= take_target;
        end
    end

    assign pc_next =
        take_target_q ? target_pc : sequential_pc;

    // 只有實際採用目標時才檢查目標對齊
    assign target_misaligned =
        !rst &&
        commit_en &&
        take_target_q &&
        (target_pc[1:0] != 2'b00);

    // 未對齊時禁止更新 PC
    assign pc_we =
        !rst &&
        commit_en &&
        !target_misaligned;

    pc_reg u_pc (
        .clk     (clk),
        .rst     (rst),
        .pc_we   (pc_we),
        .pc_next (pc_next),
        .pc      (pc)
    );

endmodule
