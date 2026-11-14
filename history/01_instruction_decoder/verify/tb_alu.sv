module tb_alu;

    timeunit 1ns;
    timeprecision 1ps;

    import fault_v_pkg::*;

    logic [31:0] a;
    logic [31:0] b;
    logic [31:0] result;
    alu_op_t     alu_op;

    int test_count = 0;

    // 被測試的 ALU
    alu dut (
        .a      (a),
        .b      (b),
        .alu_op (alu_op),
        .result (result)
    );

    // 設定輸入，等待，再檢查輸出
    task automatic check(
        input alu_op_t     op,
        input logic [31:0] av,
        input logic [31:0] bv,
        input logic [31:0] expected
    );
        a      = av;
        b      = bv;
        alu_op = op;

        #10;

        if (result !== expected) begin
            $fatal(1,
                "FAIL: op=%0d a=%h b=%h got=%h expected=%h",
                op, av, bv, result, expected
            );
        end

        test_count++;

        $display(
            "PASS %0d: op=%0d a=%h b=%h result=%h",
            test_count, op, av, bv, result
        );
    endtask

    initial begin
        // 加減
        check(ALU_ADD, 32'd5,        32'd3,        32'd8);
        check(ALU_SUB, 32'd5,        32'd3,        32'd2);
        check(ALU_SUB, 32'd3,        32'd5,        32'hFFFFFFFE);
        check(ALU_SUB, 32'd5,        32'd5,        32'd0);
        check(ALU_ADD, 32'hFFFFFFFF, 32'd1,        32'd0);
        check(ALU_ADD, 32'h7FFFFFFF, 32'd1,        32'h80000000);

        // 位元邏輯
        check(ALU_AND, 32'h0000000A, 32'h0000000C, 32'h00000008);
        check(ALU_OR,  32'h0000000A, 32'h0000000C, 32'h0000000E);
        check(ALU_XOR, 32'h0000000A, 32'h0000000C, 32'h00000006);

        // 移位
        check(ALU_SLL, 32'h00000001, 32'd31,       32'h80000000);
        check(ALU_SRL, 32'h80000000, 32'd1,        32'h40000000);
        check(ALU_SRA, 32'h80000000, 32'd1,        32'hC0000000);
        check(ALU_SRA, 32'h80000000, 32'd31,       32'hFFFFFFFF);
        check(ALU_SLL, 32'h12345678, 32'd0,        32'h12345678);

        // 32 的低 5-bit 是 0，因此不移位
        check(ALU_SLL, 32'h00000001, 32'd32,       32'h00000001);

        // Signed／unsigned 比較
        check(ALU_SLT,  32'hFFFFFFFF, 32'd1,       32'd1);
        check(ALU_SLTU, 32'hFFFFFFFF, 32'd1,       32'd0);
        check(ALU_SLT,  32'd5,        32'd5,       32'd0);
        check(ALU_SLTU, 32'd0,        32'hFFFFFFFF,32'd1);
        check(ALU_SLT,  32'h80000000, 32'h7FFFFFFF,32'd1);

        $display("ALL %0d ALU TESTS PASSED", test_count);
        $finish;
    end

endmodule
