# Immediate Generator架構

> **ALU 的 20 筆測試與 IMM 的 21 筆測試均通過，ALU 重跑亦通過，驗證涵蓋本文件列出的案例**
> 

## 1．模組用途

Immediate Generator（立即數產生器）從 **32-bit 指令**中擷取立即數，依格式重新排列位元，產生 **32-bit 的常數或位址偏移量**。

例如：

```
addi x5, x6, -4
```

```
指令內的 12-bit 立即數：111111111100
                           ↓ 符號擴展
32-bit 輸出：0xFFFFFFFC（-4）
```

| 項目 | 規格 |
| --- | --- |
| 模組名稱 | `imm_gen` |
| 電路種類 | 組合邏輯 |
| Clock／Reset | 不需要 |
| 指令輸入 | 32-bit |
| 立即數輸出 | 32-bit |
| 支援格式 | I／S／B／U／J |
| 不需要立即數 | `IMM_NONE`，輸出 0 |
| 格式選擇來源 | Decoder |
| 結果用途 | ALU 運算、記憶體有效位址、分支與跳躍目標計算 |
| 不負責的工作 | Opcode 解碼、位址相加、對齊檢查、非法指令判斷 |

## 2．模組介面

| 訊號 | 方向 | 型別／寬度 | 說明 |
| --- | --- | --- | --- |
| `instruction` | 輸入 | `logic [31:0]` | IR 保存的完整機器指令 |
| `imm_sel` | 輸入 | `fault_v_pkg::imm_sel_t`，3-bit | Decoder 指定的立即數格式 |
| `imm` | 輸出 | `logic [31:0]` | 重組及擴展後的立即數 |

## 3．架構圖

```
IR ──────────────────→ instruction
                              │
                              ▼
                    ┌───────────────────┐
                    │     imm_gen       │
                    │                   │
                    │ I：擷取＋符號擴展  │
                    │ S：重組＋符號擴展  │
                    │ B：重組＋補零＋擴展│
                    │ U：高 20-bit＋補零 │
                    │ J：重組＋補零＋擴展│
                    │ NONE：輸出 0      │
                    └─────────┬─────────┘
                              ▲
Decoder ─────────────→ imm_sel │
                              │
                              ▼
                           imm[31:0]
                              │
                              ▼
                       ALU 右輸入 MUX
                              │
                              ▼
                             ALU
```

## 4．共用格式編碼

以下定義已包含在 alu架構 的 `fault_v_pkg.sv`，不需重複加入。

```
typedef enum logic [2:0] {
    IMM_NONE = 3'd0,
    IMM_I    = 3'd1,
    IMM_S    = 3'd2,
    IMM_B    = 3'd3,
    IMM_U    = 3'd4,
    IMM_J    = 3'd5
} imm_sel_t;
```

| 名稱 | 編碼 | 用途 |
| --- | --- | --- |
| `IMM_NONE` | `3'd0` | 不需要立即數 |
| `IMM_I` | `3'd1` | 立即數運算、Load、JALR |
| `IMM_S` | `3'd2` | Store |
| `IMM_B` | `3'd3` | Branch |
| `IMM_U` | `3'd4` | LUI、AUIPC |
| `IMM_J` | `3'd5` | JAL |

## 5．立即數重組規則

以下 `inst` 代表 `instruction`。大括號由左至右代表高位到低位。

| 格式 | 重組內容 | 輸出處理 |
| --- | --- | --- |
| I | `inst[31:20]` | 12-bit 符號擴展為 32-bit |
| S | `{inst[31:25], inst[11:7]}` | 12-bit 符號擴展為 32-bit |
| B | `{inst[31], inst[7], inst[30:25], inst[11:8], 1'b0}` | 13-bit 符號擴展為 32-bit |
| U | `{inst[31:12], 12'b0}` | 20-bit 高位接上 12 個零，形成 32-bit |
| J | `{inst[31], inst[19:12], inst[20], inst[30:21], 1'b0}` | 21-bit 符號擴展為 32-bit |
| NONE | 不擷取 | 輸出 `32'b0` |
- 符號擴展：**複製原數值的最高位到新增的高位，維持二補數數值不變。

**B／J 格式已補上最低位的 0，輸出就是位元組偏移量，不可再左移一次。**

```
Branch／JAL 目標 = InstrPC + imm
```

## 6．完整 RTL：imm_gen.sv

```verilog
module imm_gen (
    input  logic [31:0]           instruction,
    input  fault_v_pkg::imm_sel_t imm_sel,

    output logic [31:0]           imm
);

    import fault_v_pkg::*;

    always_comb begin
        imm = 32'b0;

        case (imm_sel)
            IMM_I: begin
                imm = {
                    {20{instruction[31]}},
                    instruction[31:20]
                };
            end

            IMM_S: begin
                imm = {
                    {20{instruction[31]}},
                    instruction[31:25],
                    instruction[11:7]
                };
            end

            IMM_B: begin
                imm = {
                    {19{instruction[31]}},
                    instruction[31],
                    instruction[7],
                    instruction[30:25],
                    instruction[11:8],
                    1'b0
                };
            end

            IMM_U: begin
                imm = {
                    instruction[31:12],
                    12'b0
                };
            end

            IMM_J: begin
                imm = {
                    {11{instruction[31]}},
                    instruction[31],
                    instruction[19:12],
                    instruction[20],
                    instruction[30:21],
                    1'b0
                };
            end

            IMM_NONE: begin
                imm = 32'b0;
            end

            default: begin
                imm = 32'b0;
            end
        endcase
    end

endmodule
```

## 7．與 CPU 指令的對應

| 指令類別 | 格式選擇 | 立即數用途 |
| --- | --- | --- |
| ADDI／ANDI／ORI／XORI／SLTI／SLTIU | I | ALU 的第二個運算元 |
| SLLI／SRLI／SRAI | I | ALU 只取低 5-bit 作為移位量 |
| LB／LBU／LH／LHU／LW | I | 有效位址＝A＋imm |
| SB／SH／SW | S | 有效位址＝A＋imm |
| BEQ／BNE／BLT／BGE／BLTU／BGEU | B | 分支目標＝InstrPC＋imm |
| LUI | U | 將 imm 寫回 rd |
| AUIPC | U | 將 InstrPC＋imm 寫回 rd |
| JAL | J | 跳躍目標＝InstrPC＋imm |
| JALR | I | 目標＝A＋imm，再由外部邏輯清除 bit 0 |
| R-type 等不需要立即數的指令 | NONE | imm＝0 |

立即數移位指令中的功能位元是否合法，仍由 Decoder 檢查。

**8．Immediate Generator 驗證範圍**

測試直接指定 `instruction` 與 `imm_sel`，確認立即數的擷取、重組及擴展。

這是 **imm_gen 單元測試**；部分輸入是專門測試立即數位元的資料，不一定是合法完整指令。Opcode 合法性由後續 Decoder 測試負責。

| 類別 | 測試內容 | 預期行為 |
| --- | --- | --- |
| NONE | 指令全 0、全 1 | 一律輸出 0 |
| I-type | 0、正數、負數、最大正值、最小負值 | 正確擷取 12-bit 並符號擴展 |
| S-type | 0、負數、最大正值、最小負值 | 正確接合兩段立即數 |
| B-type | 小偏移、負偏移、正負邊界 | 重組正確、最低位補 0，不多移位 |
| U-type | 一般值、最高位為 1 | 保留高 20-bit，低 12-bit 清零 |
| J-type | 小偏移、負偏移、正負邊界 | 重組正確、最低位補 0，正確符號擴展 |

---

**9．完整 Testbench：`tb_imm_gen.sv`**

沿用同一份 `fault_v_pkg.sv`，不需重新建立 package。

```verilog
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
```

每筆測試等待 10 ns，共 **21 筆**，預期在 **210 ns** 結束。這個等待時間不是實際硬體延遲。

---

**10．測試案例與預期結果**

以下數值皆為十六進位。

| 編號 | 格式 | instruction | 預期 imm | 檢查重點 |
| --- | --- | --- | --- | --- |
| 1 | NONE | `00000000` | `00000000` | 無立即數 |
| 2 | NONE | `FFFFFFFF` | `00000000` | 輸入全 1 仍輸出零 |
| 3 | I | `00000000` | `00000000` | 零 |
| 4 | I | `00500000` | `00000005` | 正數 5 |
| 5 | I | `FFC00000` | `FFFFFFFC` | 負數 −4 |
| 6 | I | `7FF00000` | `000007FF` | 最大正值 2047 |
| 7 | I | `80000000` | `FFFFF800` | 最小負值 −2048 |
| 8 | S | `00000000` | `00000000` | 零 |
| 9 | S | `FE000E00` | `FFFFFFFC` | 重組 −4 |
| 10 | S | `7E000F80` | `000007FF` | 最大正值 2047 |
| 11 | S | `80000000` | `FFFFF800` | 最小負值 −2048 |
| 12 | B | `00000100` | `00000002` | 偏移 2，確認不重複左移 |
| 13 | B | `FE000E80` | `FFFFFFFC` | 負偏移 −4 |
| 14 | B | `7E000F80` | `00000FFE` | 最大正偏移 4094 |
| 15 | B | `80000000` | `FFFFF000` | 最小負偏移 −4096 |
| 16 | U | `12345ABC` | `12345000` | 低 12-bit 清零 |
| 17 | U | `FFFFFABC` | `FFFFF000` | 高位保留，低位清零 |
| 18 | J | `00200000` | `00000002` | 偏移 2，確認不重複左移 |
| 19 | J | `FFDFF000` | `FFFFFFFC` | 負偏移 −4 |
| 20 | J | `7FFFF000` | `000FFFFE` | 最大正偏移 1048574 |
| 21 | J | `80000000` | `FFF00000` | 最小負偏移 −1048576 |

B／J 的偏移 2 是合法的立即數編碼。**它是否形成符合本 CPU 4-byte 對齊要求的跳躍目標，是後續目標檢查邏輯的工作，不是 imm_gen 的工作。**

---

**11．Vivado 模擬設定**

| 項目 | 設定 |
| --- | --- |
| 模擬工具 | Vivado XSim |
| 模擬類型 | Behavioral Simulation |
| Design Sources | `fault_v_pkg.sv`、`imm_gen.sv` |
| Simulation Sources | `tb_imm_gen.sv` |
| 檔案類型 | SystemVerilog |
| 編譯順序 | `fault_v_pkg.sv` → `imm_gen.sv` → `tb_imm_gen.sv` |
| 模擬頂層 | `tb_imm_gen` |
| 觀察訊號 | `instruction`、`imm_sel`、`imm`、`test_count` |
| 預期測試數 | 21 |
| 預期結束時間 | 210 ns |

操作：

1. 將 `imm_gen.sv` 加入 **Design Sources**。
2. 將 `tb_imm_gen.sv` 加入 **Simulation Sources**。
3. 右鍵 `tb_imm_gen` → **Set as Top**。
4. 執行 **Run Behavioral Simulation**。
5. 查看 Console 是否出現：

```
ALL 21 IMM TESTS PASSED
```

這是**預期成功訊息**，目前不是已取得的模擬紀錄。

---

**12．ALU／IMM 回歸檢查**

兩個模組共用 `fault_v_pkg.sv`，因此新增或修改定義後，要確認原本 ALU 沒有受到影響。

| 順序 | 檢查項目 | 通過條件 |
| --- | --- | --- |
| 1 | 共用 package | 專案只加入一份有效的 `fault_v_pkg.sv`，操作名稱與編碼一致 |
| 2 | IMM 功能模擬 | 出現 `ALL 21 IMM TESTS PASSED` |
| 3 | ALU 回歸模擬 | 將頂層切回 `tb_alu`，重新執行，出現 `ALL 20 ALU TESTS PASSED` |
| 4 | 編譯與 elaboration | 無阻擋執行的錯誤；檢查警告是否涉及實際問題 |
| 5 | 波形與結果 | 與測試預期一致，沒有未預期的未知值 |
| 6 | 保存紀錄 | 保留 RTL、testbench 及兩次模擬輸出 |

這裡是**兩個模組各自的回歸測試**，不是整顆 CPU 或 Datapath 的整合驗證。