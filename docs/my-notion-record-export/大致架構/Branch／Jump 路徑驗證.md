# Branch／Jump 路徑驗證

> 
> 
> 
> 使用 `tb_pc_path.sv` 驗證 ALU、目標位址保存、PC 選擇與 PC 暫存器的局部整合。13 個案例全部通過，模擬於 660 ns 正常結束。涵蓋順序更新、分支目標、JAL／JALR 目標、對齊錯誤阻擋及位址回繞。分支成立訊號與執行／提交控制由 testbench 提供；尚未包含 Decoder、完整 FSM、分支比較器與返回位址寫回的整合驗證。
> 

**① 本次驗證範圍**

| 項目 | 行為 |
| --- | --- |
| 順序執行 | 下一個 PC＝InstrPC＋4 |
| Branch／JAL | 目標＝InstrPC＋Imm |
| JALR | 目標＝A＋Imm，再清除 bit 0 |
| 目標保存 | Execute 上升緣保存計算結果 |
| PC 更新 | Commit 上升緣才允許更新 |
| Branch 不成立 | 使用 InstrPC＋4，不检查未採用的目標 |
| 跳躍目標未對齊 | 回報錯誤，PC 保持不變 |
| 等待 | 沒有 Commit 時，PC 保持原值 |
| 地址加法 | 保留低 32-bit |

**本次不驗證：**

- 比較 rs1／rs2 以決定 BranchTaken。
- JAL／JALR 返回位址寫入 Register File。
- 記憶體取指是否成功。
- 完整 FSM 的停止與錯誤資訊保存。

---

**② 模組定位**

本次建立 `pc_path.sv`，作為**局部整合模組**，使用既有 `alu.sv` 和 `pc_reg.sv`。

```
InstrPC ──┐
          ├──→ 左輸入選擇 ──→ ALU ADD ──→ JALR 清 bit 0
A ────────┘                       ▲              │
                                  │              ▼
Imm ──────────────────────────────┘          目標暫存器
                                                 │
InstrPC ──→ ＋4 ──→ 順序位址暫存器                │
                         │                       │
                         └──────────┬────────────┘
                                    ▼
                                 PC MUX
                                    │
                              目標對齊檢查
                                    │
                                    ▼
                                 pc_reg
```

這裡的目標暫存器對應 W2 的 **ALUOut 用途**。順序位址和跳躍判斷也先保存，讓測試明確分開 Execute 與 Commit。

**整合完整 CPU 時，會接回既定 Datapath，不另外增加一顆專用 Branch ALU。**

---

**③ 模組介面與控制規則**

| 訊號 | 方向 | 寬度 | 意義 |
| --- | --- | --- | --- |
| `clk`、`rst` | 輸入 | 各 1-bit | 時脈、同步 Reset |
| `exec_we` | 輸入 | 1-bit | 保存本次計算結果 |
| `commit_en` | 輸入 | 1-bit | 嘗試提交 PC 更新 |
| `instr_pc` | 輸入 | 32-bit | 目前指令位址 |
| `rs1_value` | 輸入 | 32-bit | JALR 的來源資料 |
| `imm` | 輸入 | 32-bit | 已重組及擴展的立即數 |
| `is_jalr` | 輸入 | 1-bit | 選擇 JALR 地址計算 |
| `take_target` | 輸入 | 1-bit | 1＝使用跳躍目標；0＝順序位址 |
| `target_pc` | 輸出 | 32-bit | Execute 保存的目標 |
| `pc_next` | 輸出 | 32-bit | 選定的下一個 PC |
| `target_misaligned` | 輸出 | 1-bit | 本次 Commit 的目標未對齊 |
| `pc` | 輸出 | 32-bit | PC 暫存器內容 |

| 操作 | 控制方式 |
| --- | --- |
| Execute | `exec_we=1`、`commit_en=0` |
| 等待 | 兩者皆為 0 |
| Commit | `exec_we=0`、`commit_en=1` |
| Branch 成立／JAL／JALR | Execute 時 `take_target=1` |
| Branch 不成立／順序更新 | Execute 時 `take_target=0` |

每次 Commit 前必須先 Execute；兩者不能同時啟用。這是本模組的控制契約，後續由 FSM 保證。

---

**④ RTL：`pc_path.sv`**

```verilog
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
```

`target_misaligned` 是當次 Commit 的組合錯誤訊號，不是保存到 Reset 的停止旗標。完整 CPU 會由 Controller 採樣並進入 HALTED。

---

**⑤ Testbench：`tb_pc_path.sv`**

每筆案例會檢查：

1. Execute 後 PC 沒有提早更新。
2. 目標保存正確。
3. 等待期间 PC 保持。
4. Commit 前的選擇與錯誤旗標正確。
5. Commit 後 PC 符合預期。

```verilog
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
```

本測試會在未對齊案例後繼續測其他案例，因為這個局部模組只負責錯誤輸出與阻止 PC 更新，**沒有實作 HALTED 狀態**。

---

**⑥ 預期結果**

以下地址皆為十六進位。

| 編號 | 案例 | 保存目標 | 選定 pc_next | 對齊錯誤 | Commit 後 PC |
| --- | --- | --- | --- | --- | --- |
| 1 | 順序更新 | `00000000` | `00000004` | 0 | `00000004` |
| 2 | Branch 向前 | `00000014` | `00000014` | 0 | `00000014` |
| 3 | Branch 向後 | `00000004` | `00000004` | 0 | `00000004` |
| 4 | Branch 不成立 | `00000024` | `00000008` | 0 | `00000008` |
| 5 | 不成立，忽略未對齊目標 | `0000000A` | `0000000C` | 0 | `0000000C` |
| 6 | 成立，拒絕未對齊目標 | `0000000E` | `0000000E` | 1 | `0000000C`，保持 |
| 7 | JAL 目標 | `00000080` | `00000080` | 0 | `00000080` |
| 8 | JALR 對齊目標 | `0000010C` | `0000010C` | 0 | `0000010C` |
| 9 | JALR 清 bit 0 | `00000100` | `00000100` | 0 | `00000100` |
| 10 | JALR 清 bit 0 後仍未對齊 | `00000102` | `00000102` | 1 | `00000100`，保持 |
| 11 | JALR 負偏移 | `000001FC` | `000001FC` | 0 | `000001FC` |
| 12 | 負偏移產生高位地址 | `FFFFFFFC` | `FFFFFFFC` | 0 | `FFFFFFFC` |
| 13 | 順序地址加 4 回繞 | `FFFFFFFC` | `00000000` | 0 | `00000000` |

第 12 筆用來驗證 32-bit 加法截斷，不代表該目標有可用指令記憶體。

預期結束訊息：

```
ALL 13 PC PATH CASES PASSED
```

每筆案例都包含多個檢查，因此 **13 是案例數，不是比較次數**。

---

**⑦ Vivado 模擬設定**

| 類別 | 檔案 |
| --- | --- |
| Design Sources | `fault_v_pkg.sv` |
| Design Sources | `alu.sv` |
| Design Sources | `pc_reg.sv` |
| Design Sources | `pc_path.sv` |
| Simulation Sources | `tb_pc_path.sv` |
| 模擬頂層 | `tb_pc_path` |

操作：

1. 保留原有檔案，新增 `pc_path.sv`、`tb_pc_path.sv`。
2. 確認 package 先於使用它的模組編譯。
3. 關閉上一個模擬。
4. 將 `tb_pc_path` 設為 **Simulation Top**。
5. 執行 **Run Behavioral Simulation**，需要時再按 **Run All**。