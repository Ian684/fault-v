module tb_pc_path;

    timeunit 1ns;
    timeprecision 1ps;

    logic clk = 1'b0;
    logic rst;

    logic exec_we;
    logic commit_en;

    logic [31:0] instr_pc;
    logic [31:0] rs1_value;
    logic [31:0] imm;
    logic        is_jalr;
    logic        take_target;

    logic [31:0] target_pc;
    logic [31:0] pc_next;
    logic        target_misaligned;
    logic [31:0] pc;

    int test_count = 0;

    always #5 clk = ~clk;

    pc_path dut (
        .clk               (clk),
        .rst               (rst),
        .exec_we           (exec_we),
        .commit_en         (commit_en),
        .instr_pc          (instr_pc),
        .rs1_value         (rs1_value),
        .imm               (imm),
        .is_jalr           (is_jalr),
        .take_target       (take_target),
        .target_pc         (target_pc),
        .pc_next           (pc_next),
        .target_misaligned (target_misaligned),
        .pc                (pc)
    );

    task automatic run_case(
        input string       label_text,
        input logic [31:0] ip,
        input logic [31:0] base,
        input logic [31:0] immediate,
        input logic        jalr_mode,
        input logic        taken,
        input logic [31:0] expected_target,
        input logic [31:0] expected_next,
        input logic        expected_error,
        input logic [31:0] expected_pc
    );
        logic [31:0] old_pc;

        old_pc = pc;

        // Execute：準備本次計算
        @(negedge clk);
        instr_pc   = ip;
        rs1_value  = base;
        imm        = immediate;
        is_jalr    = jalr_mode;
        take_target = taken;
        exec_we    = 1'b1;
        commit_en  = 1'b0;

        @(posedge clk);
        #1;

        if (target_pc !== expected_target)
            $fatal(1,
                "FAIL %s: target=%h expected=%h",
                label_text, target_pc, expected_target
            );

        if (pc !== old_pc)
            $fatal(1,
                "FAIL %s: PC changed during Execute",
                label_text
            );

        // 停止 Execute，並改變輸入
        // 確認之後使用的是已保存的資料
        @(negedge clk);
        exec_we     = 1'b0;
        instr_pc    = 32'hDEADBEEF;
        rs1_value   = 32'hAAAAAAAA;
        imm         = 32'h55555555;
        is_jalr     = ~jalr_mode;
        take_target = ~taken;

        // 等待两拍，不應更新 PC 或目標
        repeat (2) begin
            @(posedge clk);
            #1;

            if (pc !== old_pc)
                $fatal(1,
                    "FAIL %s: PC changed while waiting",
                    label_text
                );

            if (target_pc !== expected_target)
                $fatal(1,
                    "FAIL %s: saved target changed",
                    label_text
                );
        end

        // Commit：檢查選擇與對齊
        @(negedge clk);
        commit_en = 1'b1;

        #1;

        if (pc_next !== expected_next)
            $fatal(1,
                "FAIL %s: next=%h expected=%h",
                label_text, pc_next, expected_next
            );

        if (target_misaligned !== expected_error)
            $fatal(1,
                "FAIL %s: error=%b expected=%b",
                label_text, target_misaligned, expected_error
            );

        @(posedge clk);
        #1;

        if (pc !== expected_pc)
            $fatal(1,
                "FAIL %s: pc=%h expected=%h",
                label_text, pc, expected_pc
            );

        test_count++;

        $display(
            "PASS %0d: %s target=%h next=%h error=%b pc=%h",
            test_count, label_text,
            target_pc, pc_next, target_misaligned, pc
        );

        @(negedge clk);
        commit_en = 1'b0;
    endtask

    initial begin
        rst         = 1'b1;
        exec_we     = 1'b0;
        commit_en   = 1'b0;
        instr_pc    = 32'b0;
        rs1_value   = 32'b0;
        imm         = 32'b0;
        is_jalr     = 1'b0;
        take_target = 1'b0;

        @(posedge clk);
        #1;

        if ((pc !== 32'b0) ||
            (target_pc !== 32'b0) ||
            (pc_next !== 32'b0) ||
            (target_misaligned !== 1'b0))
            $fatal(1, "FAIL: initial reset");

        @(negedge clk);
        rst = 1'b0;

        // 參數：
        // 名稱、InstrPC、rs1、imm、JALR、採用目標、
        // 預期目標、預期pc_next、預期錯誤、預期PC

        run_case(
            "sequential",
            32'h00000000, 32'h0, 32'h0, 1'b0, 1'b0,
            32'h00000000, 32'h00000004, 1'b0, 32'h00000004
        );

        run_case(
            "branch forward",
            32'h00000004, 32'h0, 32'h10, 1'b0, 1'b1,
            32'h00000014, 32'h00000014, 1'b0, 32'h00000014
        );

        run_case(
            "branch backward",
            32'h00000014, 32'h0, 32'hFFFFFFF0, 1'b0, 1'b1,
            32'h00000004, 32'h00000004, 1'b0, 32'h00000004
        );

        run_case(
            "branch not taken",
            32'h00000004, 32'h0, 32'h20, 1'b0, 1'b0,
            32'h00000024, 32'h00000008, 1'b0, 32'h00000008
        );

        run_case(
            "not taken ignores misaligned target",
            32'h00000008, 32'h0, 32'h2, 1'b0, 1'b0,
            32'h0000000A, 32'h0000000C, 1'b0, 32'h0000000C
        );

        run_case(
            "taken rejects misaligned target",
            32'h0000000C, 32'h0, 32'h2, 1'b0, 1'b1,
            32'h0000000E, 32'h0000000E, 1'b1, 32'h0000000C
        );

        run_case(
            "JAL target",
            32'h0000000C, 32'h0, 32'h74, 1'b0, 1'b1,
            32'h00000080, 32'h00000080, 1'b0, 32'h00000080
        );

        run_case(
            "JALR aligned",
            32'h00000080, 32'h100, 32'hC, 1'b1, 1'b1,
            32'h0000010C, 32'h0000010C, 1'b0, 32'h0000010C
        );

        run_case(
            "JALR clears bit zero",
            32'h0000010C, 32'h101, 32'h0, 1'b1, 1'b1,
            32'h00000100, 32'h00000100, 1'b0, 32'h00000100
        );

        run_case(
            "JALR still misaligned after clearing",
            32'h00000100, 32'h103, 32'h0, 1'b1, 1'b1,
            32'h00000102, 32'h00000102, 1'b1, 32'h00000100
        );

        run_case(
            "JALR negative offset",
            32'h00000100, 32'h200, 32'hFFFFFFFC, 1'b1, 1'b1,
            32'h000001FC, 32'h000001FC, 1'b0, 32'h000001FC
        );

        run_case(
            "target to high address",
            32'h000001FC, 32'h0, 32'hFFFFFE00, 1'b0, 1'b1,
            32'hFFFFFFFC, 32'hFFFFFFFC, 1'b0, 32'hFFFFFFFC
        );

        run_case(
            "sequential address wrap",
            32'hFFFFFFFC, 32'h0, 32'h0, 1'b0, 1'b0,
            32'hFFFFFFFC, 32'h00000000, 1'b0, 32'h00000000
        );

        $display(
            "ALL %0d PC PATH CASES PASSED",
            test_count
        );
        $finish;
    end

    initial begin
        #10000;
        $fatal(1, "TIMEOUT: PC path test did not finish");
    end

endmodule
