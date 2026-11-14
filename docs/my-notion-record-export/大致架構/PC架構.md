# PC架構

> **PC 模組經 Vivado XSim 完成 17 筆指定功能檢查，全部通過，於 146 ns 正常結束，驗證涵蓋本文件列出的案例**
> 

**① 模組用途**

PC（Program Counter）保存取指位址。

在 Fault-V 的多周期設計中：

```
指令執行期間：PC 保持不變
指令正常完成：PC 更新為 pc_next
```

**PC 模組只負責保存位址。** `PC＋4`、分支／跳躍目標選擇與對齊檢查，由外部 Datapath 和 Controller 負責。

---

**② PC 規格與介面**

| 項目 | 規格 |
| --- | --- |
| 模組名稱 | `pc_reg` |
| 寬度 | 32-bit |
| 電路種類 | 時序邏輯 |
| Clock | 上升緣更新 |
| Reset | 高有效、同步 reset |
| Reset 位址 | `0x00000000` |
| 更新條件 | `rst=0` 且 `pc_we=1` |
| 更新資料 | `pc_next` |
| `pc_we=0` | 保持原值 |
| 優先順序 | Reset 高於一般更新 |
| 自動加 4 | 不在本模組內執行 |
| 地址對齊檢查 | 由外部邏輯執行 |

| 訊號 | 方向 | 寬度 | 意義 |
| --- | --- | --- | --- |
| `clk` | 輸入 | 1-bit | 核心時脈 |
| `rst` | 輸入 | 1-bit | 高有效同步 reset |
| `pc_we` | 輸入 | 1-bit | PC 更新允許 |
| `pc_next` | 輸入 | 32-bit | 外部選定的下一個位址 |
| `pc` | 輸出 | 32-bit | 目前取指位址 |

```
InstrPC＋4 ──┐
             ├──→ PC MUX ──→ pc_next ──→ PC Register ──→ pc
ALUOut ──────┘                              ▲
                                            │
                                  clk、rst、pc_we
```

---

**③ 完整 RTL：`pc_reg.sv`**

```verilog
module pc_reg (
    input  logic        clk,
    input  logic        rst,
    input  logic        pc_we,
    input  logic [31:0] pc_next,

    output logic [31:0] pc
);

    always_ff @(posedge clk) begin
        if (rst)
            pc <= 32'h00000000;
        else if (pc_we)
            pc <= pc_next;
    end

endmodule
```

| 條件 | 上升緣的動作 |
| --- | --- |
| `rst=1` | PC 清零 |
| `rst=0`、`pc_we=1` | PC 載入 pc_next |
| `rst=0`、`pc_we=0` | PC 保持原值 |
| 沒有上升緣 | PC 不更新 |

---

**④ Day 4：驗證範圍**

| 測試項目 | 要確認的行為 |
| --- | --- |
| 初始 Reset | PC 回到 0 |
| 寫入禁止 | 即使 pc_next 改變，PC 仍保持 |
| 同步更新 | 上升緣前是舊值，更新後是新值 |
| 順序位址 | 外部提供 4、8，PC 正確載入 |
| 指定目標 | 正確載入向前或向後的目標 |
| 多拍等待 | pc_we 關閉期間不自動加 4 |
| 同步 Reset | rst 拉高後，上升緣前仍保持舊值 |
| Reset 優先權 | rst 與 pc_we 同時有效時，清零優先 |
| Reset 後恢復 | Reset 解除後可重新更新 |
| 高位地址 | 正確保存完整 32-bit 位址 |

本次只測 PC 暫存器；**分支決策、加法與未對齊目標禁止提交，留到 Day 5～6。**

---

**⑤ 完整 Testbench：`tb_pc_reg.sv`**

```verilog
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
```

測試在下降緣設定控制與資料，在上升緣後 `#1` 檢查結果，避免與 nonblocking assignment 更新產生競爭。

---

**⑥ 預期結果**

下表位址皆為十六進位。

| 編號 | 測試內容 | 預期 PC |
| --- | --- | --- |
| 1 | 初始 Reset | `00000000` |
| 2 | 禁止更新，pc_next 改為 100 | `00000000` |
| 3 | 準備寫入 4，上升緣前 | `00000000` |
| 4 | 上升緣後載入 4 | `00000004` |
| 5 | 載入下一個順序位址 8 | `00000008` |
| 6 | 載入向前目標 100 | `00000100` |
| 7 | 禁止更新，pc_next 改為 200 | `00000100` |
| 8 | 等待第 1 拍 | `00000100` |
| 9 | 等待第 2 拍 | `00000100` |
| 10 | 等待第 3 拍 | `00000100` |
| 11 | 載入向後目標 20 | `00000020` |
| 12 | rst 拉高，上升緣前 | `00000020` |
| 13 | Reset 與更新同時有效 | `00000000` |
| 14 | Reset 持續有效 | `00000000` |
| 15 | Reset 解除，更新仍禁止 | `00000000` |
| 16 | 載入高位地址 | `FFFFFFFC` |
| 17 | 載入零位址 | `00000000` |

預期結束訊息：

```
ALL 17 PC CHECKS PASSED
$finish called at time : 146 ns
```

第 16、17 筆只驗證 PC 能保存這些值，**沒有驗證地址是否存在，也沒有驗證 PC＋4 的回繞計算**。

---

**⑦ Vivado 模擬設定**

| 項目 | 設定 |
| --- | --- |
| Design Sources | 加入 `pc_reg.sv` |
| Simulation Sources | 加入 `tb_pc_reg.sv` |
| 檔案類型 | SystemVerilog |
| 模擬頂層 | `tb_pc_reg` |
| Package 依賴 | 本模組不需要 package |
| 模擬方式 | Run Behavioral Simulation |
| 觀察訊號 | clk、rst、pc_we、pc_next、pc、test_count |
| 預期結束時間 | 156 ns |
| 原有 ALU／IMM／RegFile | 保留，不需要刪除 |

若上一個模擬還開著，先 **Close Simulation**，再將 `tb_pc_reg` 設為 Simulation Top。

---

**⑧ PC 與 FSM 的整合規則**

| CPU 狀態／情況 | `pc_we` | `pc_next` |
| --- | --- | --- |
| FETCH、DECODE、Execute | 0 | 不影響目前 PC |
| 記憶體等待中 | 0 | 不影響目前 PC |
| ALU_WB、LOAD_WB | 1 | InstrPC＋4 |
| Store 成功完成 | 1 | InstrPC＋4 |
| Branch 不成立 | 1 | InstrPC＋4 |
| Branch 成立且目標對齊 | 1 | ALUOut |
| JAL／JALR 目標對齊 | 1 | ALUOut |
| FENCE 正常完成 | 1 | InstrPC＋4 |
| 錯誤／HALTED | 0 | 不更新 |
| Reset | 不論其值 | PC 清零 |