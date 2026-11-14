module tb_regfile;

    timeunit 1ns;
    timeprecision 1ps;

    logic        clk = 1'b0;
    logic        rst;

    logic [4:0]  rs1_addr;
    logic [4:0]  rs2_addr;
    logic [31:0] rs1_data;
    logic [31:0] rs2_data;

    logic        rd_we;
    logic [4:0]  rd_addr;
    logic [31:0] rd_data;

    int test_count = 0;

    // 10 ns clock 週期
    always #5 clk = ~clk;

    regfile dut (
        .clk      (clk),
        .rst      (rst),

        .rs1_addr (rs1_addr),
        .rs2_addr (rs2_addr),
        .rs1_data (rs1_data),
        .rs2_data (rs2_data),

        .rd_we    (rd_we),
        .rd_addr  (rd_addr),
        .rd_data  (rd_data)
    );

    // 為每個非零地址準備不同資料
    function automatic logic [31:0] pattern(
        input int unsigned index
    );
        pattern = 32'hA5000000 + index;
    endfunction

    // 比較兩個讀取埠的目前輸出
    task automatic expect_reads(
        input logic [31:0] expected1,
        input logic [31:0] expected2,
        input string       label_text
    );

    if ((rs1_data !== expected1) ||
        (rs2_data !== expected2)) begin
        $fatal(1,
            "FAIL %s: rs1=%0d got1=%h expected1=%h rs2=%0d got2=%h expected2=%h",
            label_text,
            rs1_addr, rs1_data, expected1,
            rs2_addr, rs2_data, expected2
        );
    end

        test_count++;
        $display("PASS %0d: %s", test_count, label_text);
    endtask

    // 在下降緣切換讀取地址，1 ns 後檢查
    task automatic check_read(
        input logic [4:0]  addr1,
        input logic [4:0]  addr2,
        input logic [31:0] expected1,
        input logic [31:0] expected2,
        input string       label_text
    );
        @(negedge clk);
        rs1_addr = addr1;
        rs2_addr = addr2;

        #1;
        expect_reads(expected1, expected2, label_text);
    endtask

    // 在下降緣準備寫入，下一個上升緣完成
    task automatic write_reg(
        input logic       enable,
        input logic [4:0] addr,
        input logic [31:0] data
    );
        @(negedge clk);
        rd_we   = enable;
        rd_addr = addr;
        rd_data = data;

        @(posedge clk);
        #1;
        rd_we = 1'b0;
    endtask

    initial begin
        rst      = 1'b1;
        rs1_addr = 5'd0;
        rs2_addr = 5'd0;
        rd_we    = 1'b0;
        rd_addr  = 5'd0;
        rd_data  = 32'b0;

        // 初始同步 Reset
        repeat (2) @(posedge clk);
        @(negedge clk);
        rst = 1'b0;

        // 1. 確認 Reset 後所有地址為零
        for (int i = 0; i < 32; i++) begin
            check_read(
                i[4:0], i[4:0],
                32'b0, 32'b0,
                $sformatf("initial reset x%0d", i)
            );
        end

        // 2. 寫入 x1～x31
        for (int i = 1; i < 32; i++) begin
            write_reg(1'b1, i[4:0], pattern(i));
        end

        // 3. 同時讀取不同地址
        for (int i = 1; i < 32; i++) begin
            check_read(
                i[4:0], 5'd0,
                pattern(i), 32'b0,
                $sformatf("read x%0d and x0", i)
            );
        end

        check_read(
            5'd5, 5'd17,
            pattern(5), pattern(17),
            "dual-port different addresses"
        );

        // 4. 寫入禁止
        write_reg(1'b0, 5'd5, 32'hDEADBEEF);

        check_read(
            5'd5, 5'd17,
            pattern(5), pattern(17),
            "write disabled"
        );

        // 5. x0 寫入保護
        write_reg(1'b1, 5'd0, 32'hFFFFFFFF);

        check_read(
            5'd0, 5'd0,
            32'b0, 32'b0,
            "x0 write protection"
        );

        // 6. 同址讀寫：上升緣前仍讀到舊值
        @(negedge clk);
        rs1_addr = 5'd5;
        rs2_addr = 5'd5;
        rd_we    = 1'b1;
        rd_addr  = 5'd5;
        rd_data  = 32'h12345678;

        #1;
        expect_reads(
            pattern(5), pattern(5),
            "same-address before write edge"
        );

        // 上升緣更新後，兩埠都讀到新值
        @(posedge clk);
        #1;
        expect_reads(
            32'h12345678, 32'h12345678,
            "same-address after write edge"
        );
        rd_we = 1'b0;

        // 7. 組合讀取：兩次取樣之間沒有上升緣
        @(negedge clk);
        rs1_addr = 5'd1;
        rs2_addr = 5'd2;

        #1;
        expect_reads(
            pattern(1), pattern(2),
            "combinational read first addresses"
        );

        rs1_addr = 5'd30;
        rs2_addr = 5'd31;

        #1;
        expect_reads(
            pattern(30), pattern(31),
            "combinational read changed addresses"
        );

        // 8. 同步 Reset：拉高後、上升緣前仍保留資料
        // 同時要求寫入，確認 Reset 優先
        @(negedge clk);
        rs1_addr = 5'd5;
        rs2_addr = 5'd7;
        rd_we    = 1'b1;
        rd_addr  = 5'd7;
        rd_data  = 32'hFFFFFFFF;
        rst      = 1'b1;

        #1;
        expect_reads(
            32'h12345678, pattern(7),
            "synchronous reset before edge"
        );

        @(posedge clk);
        #1;
        expect_reads(
            32'b0, 32'b0,
            "reset overrides write"
        );

        @(negedge clk);
        rst   = 1'b0;
        rd_we = 1'b0;

        // 9. 確認已寫入過的全部地址都被清零
        for (int i = 0; i < 32; i++) begin
            check_read(
                i[4:0], i[4:0],
                32'b0, 32'b0,
                $sformatf("final reset x%0d", i)
            );
        end

        $display(
            "ALL %0d REGFILE CHECKS PASSED",
            test_count
        );
        $finish;
    end

    // 防止因測試流程問題導致無限等待
    initial begin
        #10000;
        $fatal(1, "TIMEOUT: regfile test did not finish");
    end

endmodule
