module tb_imm_gen;

    timeunit 1ns;
    timeprecision 1ps;

    import fault_v_pkg::*;

    logic [31:0] instruction;
    imm_sel_t    imm_sel;
    logic [31:0] imm;

    int test_count = 0;

    imm_gen dut (
        .instruction (instruction),
        .imm_sel     (imm_sel),
        .imm         (imm)
    );

    task automatic check(
        input imm_sel_t    sel,
        input logic [31:0] inst,
        input logic [31:0] expected
    );
        instruction = inst;
        imm_sel     = sel;

        #10;

        if (imm !== expected) begin
            $fatal(1,
                "FAIL: sel=%0d inst=%h got=%h expected=%h",
                sel, inst, imm, expected
            );
        end

        test_count++;

        $display(
            "PASS %0d: sel=%0d inst=%h imm=%h",
            test_count, sel, inst, imm
        );
    endtask

    initial begin
        // NONE：無論輸入內容為何，都輸出 0
        check(IMM_NONE, 32'h00000000, 32'h00000000);
        check(IMM_NONE, 32'hFFFFFFFF, 32'h00000000);

        // I-type：0、5、-4、2047、-2048
        check(IMM_I, 32'h00000000, 32'h00000000);
        check(IMM_I, 32'h00500000, 32'h00000005);
        check(IMM_I, 32'hFFC00000, 32'hFFFFFFFC);
        check(IMM_I, 32'h7FF00000, 32'h000007FF);
        check(IMM_I, 32'h80000000, 32'hFFFFF800);

        // S-type：0、-4、2047、-2048
        check(IMM_S, 32'h00000000, 32'h00000000);
        check(IMM_S, 32'hFE000E00, 32'hFFFFFFFC);
        check(IMM_S, 32'h7E000F80, 32'h000007FF);
        check(IMM_S, 32'h80000000, 32'hFFFFF800);

        // B-type：2、-4、4094、-4096
        check(IMM_B, 32'h00000100, 32'h00000002);
        check(IMM_B, 32'hFE000E80, 32'hFFFFFFFC);
        check(IMM_B, 32'h7E000F80, 32'h00000FFE);
        check(IMM_B, 32'h80000000, 32'hFFFFF000);

        // U-type：低 12-bit 必須被忽略
        check(IMM_U, 32'h12345ABC, 32'h12345000);
        check(IMM_U, 32'hFFFFFABC, 32'hFFFFF000);

        // J-type：2、-4、1048574、-1048576
        check(IMM_J, 32'h00200000, 32'h00000002);
        check(IMM_J, 32'hFFDFF000, 32'hFFFFFFFC);
        check(IMM_J, 32'h7FFFF000, 32'h000FFFFE);
        check(IMM_J, 32'h80000000, 32'hFFF00000);

        $display("ALL %0d IMM TESTS PASSED", test_count);
        $finish;
    end

endmodule
