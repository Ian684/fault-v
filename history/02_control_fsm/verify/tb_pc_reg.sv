module tb_pc_reg;

    timeunit 1ns;
    timeprecision 1ps;

    logic        clk = 1'b0;
    logic        rst;
    logic        pc_we;
    logic [31:0] pc_next;
    logic [31:0] pc;

    int test_count = 0;

    // 10 ns clock 週期
    always #5 clk = ~clk;

    pc_reg dut (
        .clk     (clk),
        .rst     (rst),
        .pc_we   (pc_we),
        .pc_next (pc_next),
        .pc      (pc)
    );

    task automatic expect_pc(
        input logic [31:0] expected,
        input string       label_text
    );
        if (pc !== expected) begin
            $fatal(1,
                "FAIL %s: pc=%h expected=%h",
                label_text, pc, expected
            );
        end

        test_count++;

        $display(
            "PASS %0d: %s pc=%h",
            test_count, label_text, pc
        );
    endtask

    initial begin
        rst     = 1'b1;
        pc_we   = 1'b0;
        pc_next = 32'b0;

        // 1. 初始同步 Reset
        @(posedge clk);
        #1;
        expect_pc(32'h00000000, "initial reset");

        // 2. 寫入禁止，即使 pc_next 改變也保持 0
        @(negedge clk);
        rst     = 1'b0;
        pc_we   = 1'b0;
        pc_next = 32'h00000100;

        @(posedge clk);
        #1;
        expect_pc(32'h00000000, "hold with write disabled");

        // 3. 準備更新為 4，上升緣前仍是 0
        @(negedge clk);
        pc_we   = 1'b1;
        pc_next = 32'h00000004;

        #1;
        expect_pc(32'h00000000, "before update edge");

        // 4. 上升緣後更新為 4
        @(posedge clk);
        #1;
        expect_pc(32'h00000004, "sequential address 4");

        // 5. 外部提供下一個順序位址 8
        @(negedge clk);
        pc_next = 32'h00000008;

        @(posedge clk);
        #1;
        expect_pc(32'h00000008, "sequential address 8");

        // 6. 外部提供向前目標
        @(negedge clk);
        pc_next = 32'h00000100;

        @(posedge clk);
        #1;
        expect_pc(32'h00000100, "forward target");

        // 7. 關閉更新，改變 pc_next，PC 仍保持
        @(negedge clk);
        pc_we   = 1'b0;
        pc_next = 32'h00000200;

        @(posedge clk);
        #1;
        expect_pc(32'h00000100, "hold while next changes");

        // 8～10. 模擬等待三拍，每拍都改變 pc_next
        for (int i = 0; i < 3; i++) begin
            @(negedge clk);
            pc_next = 32'h00000300 + i * 4;

            @(posedge clk);
            #1;
            expect_pc(
                32'h00000100,
                $sformatf("wait cycle %0d", i + 1)
            );
        end

        // 11. 更新到較小的位址
        @(negedge clk);
        pc_we   = 1'b1;
        pc_next = 32'h00000020;

        @(posedge clk);
        #1;
        expect_pc(32'h00000020, "backward target");

        // 12. 拉高同步 Reset，但還沒到上升緣
        @(negedge clk);
        rst     = 1'b1;
        pc_we   = 1'b1;
        pc_next = 32'h00000400;

        #1;
        expect_pc(32'h00000020, "synchronous reset before edge");

        // 13. Reset 優先，不載入 0x400
        @(posedge clk);
        #1;
        expect_pc(32'h00000000, "reset overrides update");

        // 14. Reset 持續有效
        @(negedge clk);
        pc_next = 32'h00000800;

        @(posedge clk);
        #1;
        expect_pc(32'h00000000, "reset remains active");

        // 15. Reset 解除，但 pc_we=0，仍保持 0
        @(negedge clk);
        rst   = 1'b0;
        pc_we = 1'b0;

        @(posedge clk);
        #1;
        expect_pc(32'h00000000, "hold after reset");

        // 16. Reset 後恢復更新，檢查高位地址
        @(negedge clk);
        pc_we   = 1'b1;
        pc_next = 32'hFFFFFFFC;

        @(posedge clk);
        #1;
        expect_pc(32'hFFFFFFFC, "full-width address");

        // 17. 外部提供 0，確認可正常載入
        @(negedge clk);
        pc_next = 32'h00000000;

        @(posedge clk);
        #1;
        expect_pc(32'h00000000, "load zero address");

        $display("ALL %0d PC CHECKS PASSED", test_count);
        $finish;
    end

    // 防止測試無限等待
    initial begin
        #10000;
        $fatal(1, "TIMEOUT: PC test did not finish");
    end

endmodule
