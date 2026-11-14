# register file架構

> **Register File 已使用 Vivado XSim 完成 104 次指定功能檢查，全部通過，模擬於 1371 ns 正常結束，驗證涵蓋本文件列出的案例**
> 

驗證完成

**① 模組用途**

Register File 保存 CPU 的 **x0～x31**，提供兩筆來源資料，並接收一筆寫回結果。

例如：

```
add x7, x5, x6
```

```
讀取 x5 ──→ ALU 輸入 A
讀取 x6 ──→ ALU 輸入 B

ALU 結果 ──→ 寫入 x7
```

Register File 只負責讀寫資料，不辨認 ADD 等指令。

---

**② Register File 規格**

| 項目 | 決定 |
| --- | --- |
| 模組名稱 | `regfile` |
| 暫存器數量 | 32 個，x0～x31 |
| 資料寬度 | 每個 32-bit |
| 地址寬度 | 5-bit，可選擇 0～31 |
| 讀取埠 | 兩個，分別讀取 rs1、rs2 |
| 讀取方式 | 組合讀取，地址改變後輸出隨之更新 |
| 寫入埠 | 一個，寫入 rd |
| 寫入方式 | clock 上升緣同步寫入 |
| 寫入條件 | `rd_we=1` 且 `rd_addr!=0` |
| x0 | 永遠讀到 0，忽略寫入 |
| Reset | 高有效、同步 reset |
| Reset 行為 | 在上升緣清除所有暫存器 |
| 優先順序 | Reset 高於一般寫入 |
| 未啟用寫入 | 保持原值 |
| 同址讀寫 | 上升緣前讀到舊值；寫入更新後，組合輸出反映新值 |
| 旁路邏輯 | 不另外加入寫入資料旁路 |

同步 reset 不會在 `rst` 剛拉高時立刻清除資料，必須等到 clock 上升緣。

---

**③ 模組介面**

| 訊號 | 方向 | 寬度 | 意義 |
| --- | --- | --- | --- |
| `clk` | 輸入 | 1-bit | 核心時脈 |
| `rst` | 輸入 | 1-bit | 高有效同步 reset |
| `rs1_addr` | 輸入 | 5-bit | 第一個讀取地址 |
| `rs2_addr` | 輸入 | 5-bit | 第二個讀取地址 |
| `rs1_data` | 輸出 | 32-bit | 第一個讀取資料 |
| `rs2_data` | 輸出 | 32-bit | 第二個讀取資料 |
| `rd_we` | 輸入 | 1-bit | 寫入允許 |
| `rd_addr` | 輸入 | 5-bit | 寫入目的地址 |
| `rd_data` | 輸入 | 32-bit | 寫入資料 |

此模組目前不使用 package 裡的 enum，因此不需要 import `fault_v_pkg`。

---

**④ 架構與資料流**

```
rs1_addr ──────→┌────────────────────┐──────→ rs1_data
               │                    │
rs2_addr ──────→│   Register File    │──────→ rs2_data
               │                    │
rd_addr ──────→│     32 × 32-bit    │
rd_data ──────→│                    │
rd_we   ──────→│  x0 永遠讀到零     │
               │                    │
clk     ──────→│  上升緣寫入／Reset │
rst     ──────→└────────────────────┘
```

| 動作 | 行為 |
| --- | --- |
| 讀取 x0 | 輸出 `32'b0` |
| 讀取 x1～x31 | 輸出該暫存器內容 |
| 上升緣，`rst=1` | 全部清零 |
| 上升緣，`rst=0`、`rd_we=1`、`rd_addr!=0` | 寫入 rd_data |
| 上升緣，`rd_we=0` | 保持原值 |
| 上升緣，寫入地址為 x0 | 忽略寫入 |

---

**⑤ 完整 RTL：`regfile.sv`**

```verilog
module regfile (
    input  logic        clk,
    input  logic        rst,

    input  logic [4:0]  rs1_addr,
    input  logic [4:0]  rs2_addr,
    output logic [31:0] rs1_data,
    output logic [31:0] rs2_data,

    input  logic        rd_we,
    input  logic [4:0]  rd_addr,
    input  logic [31:0] rd_data
);

    logic [31:0] regs [0:31];

    // 同步 Reset 與同步寫入
    always_ff @(posedge clk) begin
        if (rst) begin
            for (int i = 0; i < 32; i++) begin
                regs[i] <= 32'b0;
            end
        end
        else if (rd_we && (rd_addr != 5'd0)) begin
            regs[rd_addr] <= rd_data;
        end
    end

    // 兩個組合讀取埠
    assign rs1_data =
        (rs1_addr == 5'd0) ? 32'b0 : regs[rs1_addr];

    assign rs2_data =
        (rs2_addr == 5'd0) ? 32'b0 : regs[rs2_addr];

endmodule
```

| 寫法 | 用途 |
| --- | --- |
| `logic [31:0] regs [0:31]` | 宣告 32 個元素，每個元素 32-bit |
| `always_ff @(posedge clk)` | 只在 clock 上升緣更新儲存內容 |
| `<=` | 同步暫存器使用 nonblocking assignment |
| Reset 中的 `for` | 描述所有儲存元素在同一個 reset 邊緣清零，不是分 32 拍執行 |
| `rd_addr != 0` | 阻止對 x0 的寫入 |
| 讀取端判斷地址 0 | 保證 x0 的輸出為零 |
| 無最後的 `else` | 時序電路未被寫入時保持原值 |

這是初版的暫存器陣列實作，**不能假設會自動變成 FPGA BRAM 或 ASIC SRAM**。

---

**⑥ 同址讀寫與時序**

假設 x5 原本是 10，準備寫入 20，而且讀取地址也是 x5：

| 時間 | 狀態 | 讀出值 |
| --- | --- | --- |
| 上升緣前 | 寫入尚未發生 | 10 |
| 上升緣觸發後 | nonblocking assignment 更新儲存內容 | 更新過程中不應過早取樣 |
| 更新及組合邏輯重新計算後 | x5 已保存 20 | 20 |

Testbench 會在下降緣準備輸入，在上升緣後稍等再檢查，避免模擬排程造成競爭。

---

**⑦ Day 2：驗證範圍**

| 類別 | 測試內容 | 預期行為 |
| --- | --- | --- |
| 初始 Reset | 讀取全部地址 | 兩個讀取埠都輸出零 |
| x1～x31 寫入 | 每個地址寫入不同資料 | 各地址讀回自己的資料 |
| 雙埠讀取 | 同時讀取不同地址 | 兩個輸出各自正確 |
| 寫入禁止 | `rd_we=0` 時提供新資料 | 原值不變 |
| x0 保護 | 嘗試寫入全 1 | x0 仍為零 |
| 同址读寫 | 讀取正在被寫入的地址 | 邊緣前舊值，更新後新值 |
| 上升緣寫入 | 邊緣前先檢查資料 | 不會提前改變儲存內容 |
| 組合讀取 | 在兩個上升緣之間切換讀取地址 | 不需等待下個上升緣 |
| Reset 優先權 | Reset 與寫入同時有效 | 清零優先 |
| 非零資料清除 | 已寫入資料後再 Reset | 全部清零 |

---

**⑧ 完整 Testbench：`tb_regfile.sv`**

```verilog
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
                "FAIL %s: rs1=%0d got1=%h expected1=%h "
                "rs2=%0d got2=%h expected2=%h",
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
```

- *注意：**若工具不接受 $fatal 中相鄰的兩段字串，將該格式字串寫成同一行：

```
"FAIL %s: rs1=%0d got1=%h expected1=%h rs2=%0d got2=%h expected2=%h"
```

---

**⑨ Vivado 模擬設定**

| 項目 | 設定 |
| --- | --- |
| Design Sources | 加入 `regfile.sv` |
| Simulation Sources | 加入 `tb_regfile.sv` |
| 檔案類型 | SystemVerilog |
| 模擬頂層 | `tb_regfile` |
| 模擬方式 | Run Behavioral Simulation |
| 執行時間 | 使用 **Run All**，讓 $finish 結束 |
| 觀察訊號 | clk、rst、rd_we、rd_addr、rd_data、rs1_addr、rs2_addr、rs1_data、rs2_data、test_count |
| 原有 ALU／IMM 檔案 | 保留，不需要刪除 |

此測試超過 1000 ns。如果 Vivado 預設跑到 1000 ns 暫停，按 **Run All** 或在模擬 Tcl Console 輸入：

```
run all
```

成功時預期顯示：

```
ALL 104 REGFILE CHECKS PASSED
```

104 是兩個讀取埠一起檢查的呼叫次數，不是指令數。

---

**⑩ 與 W2 Datapath 的銜接**

```
IR
├── rs1 編號 ──→ rs1_addr
├── rs2 編號 ──→ rs2_addr
└── rd 編號  ──→ rd_addr

Register File
├── rs1_data ──→ A 暫存器
└── rs2_data ──→ B 暫存器

Writeback MUX ──→ rd_data
Controller   ──→ rd_we
```

| CPU 階段 | Register File 行為 |
| --- | --- |
| DECODE | 組合輸出 rs1、rs2 資料，供 A／B 在上升緣保存 |
| ALU_WB | 寫入 ALUOut |
| LOAD_WB | 寫入 Load 擷取／擴展結果 |
| JUMP_COMMIT | 目標檢查成功後，寫入 InstrPC＋4 |
| Store／Branch | 不寫入 rd |
| Reset | 上升緣清零 |

**Register File 預期結果與實際驗證**

測試資料使用：

```
pattern(i) = 0xA5000000 + i
```

例如 x1 寫入 `A5000001`、x5 寫入 `A5000005`、x31 寫入 `A500001F`。下表數值皆為十六進位。

| 檢查編號 | 測試內容 | rs1 預期輸出 | rs2 預期輸出 | 實際結果 |
| --- | --- | --- | --- | --- |
| 1～32 | 初始 Reset 後，兩埠依序讀 x0～x31 | 全部 `00000000` | 全部 `00000000` | PASS |
| 33～63 | 第一埠依序讀 x1～x31；第二埠讀 x0 | `A5000001`～`A500001F` | `00000000` | PASS |
| 64 | 同時讀 x5、x17 | `A5000005` | `A5000011` | PASS |
| 65 | `rd_we=0`，嘗試把 `DEADBEEF` 寫入 x5；再讀 x5、x17 | `A5000005`，保持原值 | `A5000011` | PASS |
| 66 | 嘗試把 `FFFFFFFF` 寫入 x0；兩埠讀 x0 | `00000000` | `00000000` | PASS |
| 67 | 準備把 `12345678` 寫入 x5；上升緣前兩埠讀 x5 | `A5000005`，舊值 | `A5000005`，舊值 | PASS |
| 68 | 同一筆寫入，上升緣更新後兩埠讀 x5 | `12345678`，新值 | `12345678`，新值 | PASS |
| 69 | 下降緣後讀 x1、x2 | `A5000001` | `A5000002` | PASS |
| 70 | 未經下一個上升緣，改讀 x30、x31 | `A500001E` | `A500001F` | PASS |
| 71 | 拉高 Reset，同時準備寫 x7；上升緣前讀 x5、x7 | `12345678`，尚未清零 | `A5000007`，尚未清零 | PASS |
| 72 | Reset 與寫入同時有效，上升緣後讀 x5、x7 | `00000000` | `00000000`，Reset 優先 | PASS |
| 73～104 | 最後兩埠依序讀 x0～x31 | 全部 `00000000` | 全部 `00000000` | PASS |

**預期結束訊息：**

```
ALL 104 REGFILE CHECKS PASSED
$finish called at time : 1371 ns
```