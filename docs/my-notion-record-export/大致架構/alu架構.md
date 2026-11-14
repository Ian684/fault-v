# alu架構

> **Immediate Generator 的 21 筆功能測試通過，ALU 的 20 筆回歸測試通過，驗證涵蓋本文件列出的案例**
> 

**① ALU 規格**

| 項目 | 決定 |
| --- | --- |
| 模組名稱 | `alu` |
| 資料寬度 | 輸入、輸出皆為 32-bit |
| 電路種類 | 組合邏輯，不含 clock、reset 或內部暫存器 |
| 支援操作 | ADD、SUB、AND、OR、XOR、SLL、SRL、SRA、SLT、SLTU |
| 操作選擇 | 4-bit `alu_op` |
| 加減結果 | 保留低 32-bit，不產生算術溢位停止 |
| 移位量 | 使用 `b[4:0]`，範圍 0～31 |
| 比較結果 | 成立輸出 `32'd1`，否則 `32'd0` |
| 分支比較 | 由獨立 `branch_cmp` 處理 |
| JALR 清 bit 0 | 由 ALU 外部的目標處理邏輯負責 |
| 結果保存 | 由 Datapath 的 ALUOut 暫存器負責 |
| 未定義的 ALU 控制值 | 輸出 0；不取代 Decoder 的非法指令檢查 |

---

**② ALU 操作編碼**

以下是 **CPU 內部控制編碼**，不是 RISC-V opcode。Decoder 會將指令轉換成對應的 ALU 操作。

| 名稱 | 編碼 | 運算 |
| --- | --- | --- |
| `ALU_ADD` | `4'd0` | a＋b |
| `ALU_SUB` | `4'd1` | a−b |
| `ALU_AND` | `4'd2` | a AND b |
| `ALU_OR` | `4'd3` | a OR b |
| `ALU_XOR` | `4'd4` | a XOR b |
| `ALU_SLL` | `4'd5` | a 左移 `b[4:0]`，低位補 0 |
| `ALU_SRL` | `4'd6` | a 邏輯右移 `b[4:0]`，高位補 0 |
| `ALU_SRA` | `4'd7` | a 算術右移 `b[4:0]`，高位補符號位 |
| `ALU_SLT` | `4'd8` | signed a＜b，輸出 1 或 0 |
| `ALU_SLTU` | `4'd9` | unsigned a＜b，輸出 1 或 0 |

---

**③ Immediate Generator 共用編碼**

ALU 與 Immediate Generator 共用同一個 package，因此一併定義立即數格式。

| 名稱 | 編碼 | 用途 |
| --- | --- | --- |
| `IMM_NONE` | `3'd0` | 不需要立即數，輸出 0 |
| `IMM_I` | `3'd1` | 一般立即數運算、Load、JALR |
| `IMM_S` | `3'd2` | Store |
| `IMM_B` | `3'd3` | Branch |
| `IMM_U` | `3'd4` | LUI、AUIPC |
| `IMM_J` | `3'd5` | JAL |

移位立即數指令使用 I-type 編碼。ALU 只取右輸入的低 5-bit 作為移位量，其餘功能位元是否合法由 Decoder 檢查。

---

**④ 共用定義：`fault_v_pkg.sv`**

```verilog
package fault_v_pkg;

    // CPU 內部 ALU 操作編碼
    typedef enum logic [3:0] {
        ALU_ADD  = 4'd0,
        ALU_SUB  = 4'd1,
        ALU_AND  = 4'd2,
        ALU_OR   = 4'd3,
        ALU_XOR  = 4'd4,
        ALU_SLL  = 4'd5,
        ALU_SRL  = 4'd6,
        ALU_SRA  = 4'd7,
        ALU_SLT  = 4'd8,
        ALU_SLTU = 4'd9
    } alu_op_t;

    // 立即數格式選擇
    typedef enum logic [2:0] {
        IMM_NONE = 3'd0,
        IMM_I    = 3'd1,
        IMM_S    = 3'd2,
        IMM_B    = 3'd3,
        IMM_U    = 3'd4,
        IMM_J    = 3'd5
    } imm_sel_t;

endpackage
```

---

**⑤ 模組介面**

| 模組 | 訊號 | 方向 | 型別／寬度 | 意義 |
| --- | --- | --- | --- | --- |
| `alu` | `a` | 輸入 | `logic [31:0]` | 第一個運算元 |
| `alu` | `b` | 輸入 | `logic [31:0]` | 第二個運算元 |
| `alu` | `alu_op` | 輸入 | `fault_v_pkg::alu_op_t`，4-bit | 操作選擇 |
| `alu` | `result` | 輸出 | `logic [31:0]` | 組合運算結果 |
| `imm_gen` | `instruction` | 輸入 | `logic [31:0]` | 完整機器指令 |
| `imm_gen` | `imm_sel` | 輸入 | `fault_v_pkg::imm_sel_t`，3-bit | 立即數格式 |
| `imm_gen` | `imm` | 輸出 | `logic [31:0]` | 重組、擴展後的立即數 |

---

**⑥ 完整 ALU RTL：`alu.sv`**

```verilog
module alu (
    input  logic [31:0]          a,
    input  logic [31:0]          b,
    input  fault_v_pkg::alu_op_t alu_op,

    output logic [31:0]          result
);

    import fault_v_pkg::*;

    always_comb begin
        result = 32'b0;

        case (alu_op)
            ALU_ADD: begin
                result = a + b;
            end

            ALU_SUB: begin
                result = a - b;
            end

            ALU_AND: begin
                result = a & b;
            end

            ALU_OR: begin
                result = a | b;
            end

            ALU_XOR: begin
                result = a ^ b;
            end

            ALU_SLL: begin
                result = a << b[4:0];
            end

            ALU_SRL: begin
                result = a >> b[4:0];
            end

            ALU_SRA: begin
                result = $signed(a) >>> b[4:0];
            end

            ALU_SLT: begin
                result = {31'b0, ($signed(a) < $signed(b))};
            end

            ALU_SLTU: begin
                result = {31'b0, (a < b)};
            end

            default: begin
                result = 32'b0;
            end
        endcase
    end

endmodule
```

---

**⑦ ALU 的責任邊界**

| ALU 負責 | 其他模組負責 |
| --- | --- |
| 根據 a、b、alu_op 計算結果 | Decoder 辨認指令 |
| signed／unsigned 小於比較 | MUX 選擇輸入資料來源 |
| 算術與邏輯移位 | ALUOut 保存結果 |
| 未定義控制值輸出零 | Decoder／Controller 處理非法指令與錯誤停止 |
| 加法產生原始目標地址 | JALR 外部邏輯清 bit 0，檢查邏輯確認對齊 |

ALU 的 `result` 是組合輸出，不會保存前一次運算結果。需要跨 cycle 使用時，由外部 ALUOut 暫存器保存。

---

**⑧ 與 W2 Datapath 的銜接**

```
A／InstrPC／0 ──→ 左輸入 MUX ──→ a ──┐
                                    │
                                    ▼
                                ┌───────┐
Decoder／FSM ───────→ alu_op ───→│  ALU  │
                                └───┬───┘
                                    ▲
B／Imm ─────────→ 右輸入 MUX ──→ b ──┘
                                    │
                                    ▼
                                  result
                                    │
                                    ▼
                              JALR 目標處理
                                    │
                                    ▼
                                  ALUOut
```

| 指令用途 | ALU 操作 |
| --- | --- |
| ADD／ADDI、地址計算、Branch／JAL 目標、AUIPC／LUI | `ALU_ADD` |
| SUB | `ALU_SUB` |
| AND／ANDI 等 | 對應的位元邏輯操作 |
| 移位指令 | `ALU_SLL`／`ALU_SRL`／`ALU_SRA` |
| SLT／SLTI | `ALU_SLT` |
| SLTU／SLTIU | `ALU_SLTU` |

---

**⑨ Testbench：`tb_alu.sv`**

```verilog
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
        check(ALU_SLT,  32'hFFFFFFFF, 32'd1,        32'd1);
        check(ALU_SLTU, 32'hFFFFFFFF, 32'd1,        32'd0);
        check(ALU_SLT,  32'd5,        32'd5,        32'd0);
        check(ALU_SLTU, 32'd0,        32'hFFFFFFFF, 32'd1);
        check(ALU_SLT,  32'h80000000, 32'h7FFFFFFF, 32'd1);

        $display("ALL %0d ALU TESTS PASSED", test_count);
        $finish;
    end

endmodule
```

`#10` 表示每筆測試等待 10 ns 再檢查結果，**不是實際 ALU 延遲的測量值**。`!==` 可將輸出中的未知值也判定為不符合預期。

---

**⑩ 測試項目與結果**

依已提供的 Vivado 模擬紀錄，以下 20 筆測試皆通過。表中數值為十六進位。

| 編號 | 操作 | a | b | 預期／實際結果 | 狀態 |
| --- | --- | --- | --- | --- | --- |
| 1 | ADD | `00000005` | `00000003` | `00000008` | PASS |
| 2 | SUB | `00000005` | `00000003` | `00000002` | PASS |
| 3 | SUB | `00000003` | `00000005` | `FFFFFFFE` | PASS |
| 4 | SUB | `00000005` | `00000005` | `00000000` | PASS |
| 5 | ADD | `FFFFFFFF` | `00000001` | `00000000` | PASS |
| 6 | ADD | `7FFFFFFF` | `00000001` | `80000000` | PASS |
| 7 | AND | `0000000A` | `0000000C` | `00000008` | PASS |
| 8 | OR | `0000000A` | `0000000C` | `0000000E` | PASS |
| 9 | XOR | `0000000A` | `0000000C` | `00000006` | PASS |
| 10 | SLL | `00000001` | `0000001F` | `80000000` | PASS |
| 11 | SRL | `80000000` | `00000001` | `40000000` | PASS |
| 12 | SRA | `80000000` | `00000001` | `C0000000` | PASS |
| 13 | SRA | `80000000` | `0000001F` | `FFFFFFFF` | PASS |
| 14 | SLL | `12345678` | `00000000` | `12345678` | PASS |
| 15 | SLL | `00000001` | `00000020` | `00000001` | PASS |
| 16 | SLT | `FFFFFFFF` | `00000001` | `00000001` | PASS |
| 17 | SLTU | `FFFFFFFF` | `00000001` | `00000000` | PASS |
| 18 | SLT | `00000005` | `00000005` | `00000000` | PASS |
| 19 | SLTU | `00000000` | `FFFFFFFF` | `00000001` | PASS |
| 20 | SLT | `80000000` | `7FFFFFFF` | `00000001` | PASS |

第 15 筆的 `b=0x20` 是十進位 32，其低 5-bit 為 0，因此不移位。

---

**⑪ Vivado 模擬設定與完成紀錄**

| 項目 | 設定／結果 |
| --- | --- |
| 模擬工具 | Vivado XSim |
| 模擬類型 | Behavioral Simulation |
| Design Sources | `fault_v_pkg.sv`、`alu.sv` |
| Simulation Sources | `tb_alu.sv` |
| 檔案類型 | SystemVerilog |
| 編譯順序 | `fault_v_pkg.sv` → `alu.sv` → `tb_alu.sv` |
| 模擬頂層 | `tb_alu` |
| 測試數量 | 20 筆 |
| 每筆等待時間 | 10 ns |
| Testbench 結束時間 | 200 ns |
| 模擬結果 | `ALL 20 ALU TESTS PASSED` |
| 驗證範圍 | 十種操作與上述邊界案例的第一輪功能驗證 |
| 尚未代表完成 | 所有輸入組合驗證、綜合後時序驗證、FPGA 實板驗證 |

即使執行命令是 `run 1000ns`，testbench 仍會在 200 ns 呼叫 $finish 主動結束，屬於正常結果。