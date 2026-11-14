# Fault-V：Branch 與 Jump CPU Datapath

## ① 指令語意與支援範圍

這個 CPU top 在既有整數運算資料路徑上加入條件分支及跳躍，可以執行迴圈與函式呼叫／返回。保持 32-bit、多周期、FSM、單指令依序執行；每條指令正常完成後才更新 PC。

| 項目 | 規格 |
| --- | --- |
| 模組名稱 | `fault_v_cpu` |
| 既有整數運算 | 10 種 R-type、9 種 I-type、LUI、AUIPC |
| Branch | BEQ、BNE、BLT、BGE、BLTU、BGEU |
| Jump | JAL、JALR |
| 其他既定行為 | FENCE 依序完成；ECALL／EBREAK 停止並區分原因 |
| 指令對齊 | 4-byte，未加入 C 壓縮指令 |
| 記憶體 | 指令請求／回應握手，一次最多一筆 |
| 尚未接入 | Load／Store；在 top 以非法指令停止 |
| 執行環境 | 裸機，自訂 halt／debug；沒有標準 machine-mode trap／CSR／中斷 |

這仍是 RV32I 的子集。Decoder 雖能辨識 Load／Store，但資料讀寫路徑尚未接入，不能只靠解碼成功就宣稱完整支援 RV32I。

| 指令 | 比較條件／目標 | 正常完成時寫回 | 正常完成時 PC |
| --- | --- | --- | --- |
| BEQ | A＝B | 無 | 成立：InstrPC＋imm；否則 InstrPC＋4 |
| BNE | A≠B | 無 | 同上 |
| BLT | signed A＜signed B | 無 | 同上 |
| BGE | signed A≥signed B | 無 | 同上 |
| BLTU | unsigned A＜unsigned B | 無 | 同上 |
| BGEU | unsigned A≥unsigned B | 無 | 同上 |
| JAL | InstrPC＋imm | rd＝InstrPC＋4；rd＝x0 時忽略寫入 | 目標 |
| JALR | (A＋imm) 清除 bit 0 | rd＝InstrPC＋4；rd＝x0 時忽略寫入 | 清除 bit 0 後的目標 |

**分支／JAL 的立即數是相對於目前指令 InstrPC 的 byte offset。imm_gen 已補上 B／J 的最低位 0，不可再左移。JALR 使用符號擴展的 I-type 立即數，不能把它當成 B／J 格式。**

### signed 與 unsigned 比較

| A | B | signed A＜B | unsigned A＜B |
| --- | --- | --- | --- |
| 0xFFFFFFFF | 0x00000001 | 真，-1＜1 | 假，4294967295＞1 |
| 0x80000000 | 0x7FFFFFFF | 真，最小 signed 值＜最大 signed 值 | 假 |
| 0x00000007 | 0x00000007 | 假 | 假 |

BGE／BGEU 包含相等。不要用減法結果的最高位直接代替 signed 比較，因為減法可能溢位；比較器明確使用 `$signed`。

## ② 新增的 Datapath

```text
IR → Decoder → branch_op、alu_src_a／b、wb_sel、instr_class
 │
 └→ imm_gen → B／J／I 格式立即數

Register File → A、B 暫存器 → Branch Comparator → branch_condition
                                                    │
                                           branch_taken_we
                                                    ▼
                                               BranchTaken
                                                    │
                                                    ▼
                                               Control FSM

InstrPC／A → ALU 左 MUX ┐
imm        → ALU 右 MUX ├→ ALU → JALR bit 0 清除 → ALUOut
                       ┘                         │
                                                 ├→ 目標對齊檢查
                                                 └→ PC 目標來源

ALUOut／InstrPC＋4 → Writeback MUX → Register File rd
InstrPC＋4／ALUOut → PC MUX → PC（正常 commit 時更新）
```

| 元件／訊號 | 功能 | 更新或使用時機 |
| --- | --- | --- |
| branch_compare | 比較 A／B，支援六種條件 | 組合邏輯，沒有 clock／reset |
| branch_condition | 比較器當下結果 | 在 BR_EXEC 供保存 |
| branch_taken | 1-bit 暫存器，保存分支成立結果 | branch_taken_we 時更新；reset 清 0 |
| ALUOut | 保存 Branch／JAL／JALR 最終目標 | Execute 結束時更新 |
| JALR bit 0 清除 | 將加法結果最低位設為 0 | 保存 ALUOut 前處理 |
| Writeback MUX | WB_PC4 選 InstrPC＋4，其餘已支援指令選 ALUOut | 寫回及 commit trace 使用同一個 wb_data |
| PC MUX | PC_SEQ 選 InstrPC＋4，PC_TARGET 選 ALUOut | pc_we 時保存到 PC |

| 指令類別 | ALU A | ALU B | ALU 動作 |
| --- | --- | --- | --- |
| Branch | InstrPC | B-type imm | ADD，與比較器同時工作 |
| JAL | InstrPC | J-type imm | ADD |
| JALR | A 暫存器 | I-type imm | ADD，再清除 bit 0 |

當 JALR 的 rd＝rs1，A 在 Decode 已保存跳躍前的 rs1，所以先使用舊值計算目標，再把返回位址寫入同一個暫存器。`jalr x5,0(x5)` 不能先寫 x5 再用新 x5 計算目標。

## ③ 狀態與控制訊號

取指成功後保存 IR／InstrPC；Decoder 的控制輸出在該指令完成前保持，A／B 在 Decode 保存。取指等待期間 PC 保持。

| 狀態 | 動作 | 主要 enable | 下一狀態 |
| --- | --- | --- | --- |
| DECODE，Branch | 保存 A／B | ab_we | BR_EXEC |
| BR_EXEC | ALU 計算目標，比較器判斷條件 | aluout_we、branch_taken_we | BR_COMMIT |
| BR_COMMIT，不成立 | 不寫 rd，正常完成 | pc_we、instr_done；PC_SEQ | FETCH |
| BR_COMMIT，成立且對齊 | 不寫 rd，正常完成 | pc_we、instr_done；PC_TARGET | FETCH |
| BR_COMMIT，成立但未對齊 | 記錄錯誤，不更新 PC／rd | halt event | HALTED |
| DECODE，JAL／JALR | 保存運算元 | ab_we | JUMP_EXEC |
| JUMP_EXEC | 計算目標；JALR 清除 bit 0 | aluout_we | JUMP_COMMIT |
| JUMP_COMMIT，對齊 | 寫返回位址並跳躍 | reg_we、pc_we、instr_done；PC_TARGET | FETCH |
| JUMP_COMMIT，未對齊 | 記錄錯誤，不寫返回位址 | halt event | HALTED |

PC 更新和 JAL／JALR 寫回發生在同一個正常完成上升緣。BR_EXEC、JUMP_EXEC 只保存中間結果，不提前更新 PC。

## ④ 對齊、錯誤與返回位址

| 情況 | 行為 |
| --- | --- |
| Branch 不成立，計算目標未對齊 | 不跳躍，不因該目標報錯；PC＝InstrPC＋4 |
| Branch 成立，目標低 2-bit 非 00 | HALT_INSTR_ALIGN；fault_pc＝分支指令位址，fault_addr＝目標 |
| JAL 目標未對齊 | HALT_INSTR_ALIGN，PC 保持，rd 不寫入 |
| JALR 原始目標奇數 | 先清 bit 0，再檢查 4-byte 對齊 |
| JALR 清 bit 0 後 bit 1 仍為 1 | HALT_INSTR_ALIGN，PC 保持，rd 不寫入 |
| 對齊目標不在測試記憶體 | 跳躍正常 commit；下一次取指收到錯誤，HALT_FETCH_ACCESS |
| 目標取指失敗 | fault_pc／fault_addr＝取指目標；此前已完成的 link 寫回保留 |
| reset | 同步清核心暫存器及狀態；測試記憶體一起取消 pending／舊回應 |

例如 JALR 的 A＝0x13、imm＝0，清 bit 0 得到 0x12，仍未對齊；A＝0x11 則變成 0x10，可跳躍。核心不在 Execute 預先判斷記憶體容量，可存取範圍由外部記憶體的回應決定。

本設計遇錯誤會停止，沒有標準 trap handler。正常跳躍與下一條指令取指失敗是兩個不同事件，不能因下一次取指失敗而回滾已完成的跳躍寫回。

## ⑤ Branch Comparator：完整 RTL

| 接腳 | 方向 | 型別／寬度 | 說明 |
| --- | --- | --- | --- |
| a、b | 輸入 | logic [31:0] | 已保存的 rs1／rs2 資料 |
| branch_op | 輸入 | fault_v_pkg::branch_op_t，3-bit | Decoder 指定的比較條件 |
| taken | 輸出 | logic，1-bit | 條件成立；BR_NONE／未使用編碼預設 0 |

```systemverilog
`timescale 1ns/1ps
module branch_compare (
    input logic [31:0] a,b,
    input fault_v_pkg::branch_op_t branch_op,
    output logic taken
);
    import fault_v_pkg::*;
    always_comb begin
        taken=1'b0;
        case (branch_op)
            BR_EQ: taken=(a==b);
            BR_NE: taken=(a!=b);
            BR_LT: taken=($signed(a)<$signed(b));
            BR_GE: taken=($signed(a)>=$signed(b));
            BR_LTU: taken=(a<b);
            BR_GEU: taken=(a>=b);
            default: taken=1'b0;
        endcase
    end
endmodule
```

## ⑥ CPU Top：完整 RTL

Top 外部記憶體／debug／commit 接腳沿用整數 CPU 定義。`retire_valid` 與資料在完成指令的 clock 上升緣、非阻塞更新前取樣；是專案自訂 trace，不是完整 RVFI。Branch 正常完成會 retire，但 retire_rd_we＝0；JAL／JALR 寫 x0 時同樣為 0。

這份 top 使用檔案包中其餘八個 RTL 檔案。`fault_v_pkg.sv` 先編譯，`fault_v_cpu.sv` 只保留一份。資料介面的 wdata／wstrb 仍為 0，本範圍不發資料交易。

```systemverilog
`timescale 1ns/1ps
module fault_v_cpu (
    input logic clk, rst,
    output logic imem_req_valid,
    input logic imem_req_ready,
    output logic [31:0] imem_req_addr,
    input logic imem_rsp_valid, imem_rsp_err,
    input logic [31:0] imem_rsp_data,
    output logic imem_rsp_ready,
    // Reserved for the subsequent load/store integration.
    output logic dmem_req_valid,
    input logic dmem_req_ready,
    output logic dmem_req_write,
    output logic [31:0] dmem_req_addr,dmem_req_wdata,
    output logic [3:0] dmem_req_wstrb,
    input logic dmem_rsp_valid,dmem_rsp_err,
    input logic [31:0] dmem_rsp_data,
    output logic dmem_rsp_ready,
    output logic halted,
    output fault_v_pkg::halt_cause_t halt_cause,
    output logic [31:0] fault_pc,fault_addr,pc,
    output fault_v_pkg::cpu_state_t state,
    // Combinational commit trace, sampled at the same rising edge as writeback.
    // These are project-specific signals, not a full RVFI implementation.
    output logic retire_valid,retire_rd_we,
    output logic [31:0] retire_pc,retire_instruction,retire_rd_data,
    output logic [4:0] retire_rd_addr
);
    import fault_v_pkg::*;
    logic [31:0] ir,instr_pc,a_reg,b_reg,aluout;
    logic [31:0] rs1_data,rs2_data,imm,alu_a,alu_b,alu_result,pc_next;
    logic [4:0] rs1_addr,rs2_addr,rd_addr;
    instr_class_t instr_class;
    alu_op_t alu_op;
    imm_sel_t imm_sel;
    alu_src_a_t alu_src_a;
    alu_src_b_t alu_src_b;
    branch_op_t branch_op;
    mem_size_t mem_size;
    wb_sel_t wb_sel;
    pc_sel_t pc_sel;
    logic load_unsigned,rd_write,decode_illegal,core_illegal;
    logic ir_we,instr_pc_we,ab_we,aluout_we,branch_taken_we,mdr_we,reg_we,pc_we;
    logic instr_done,mem_pending,branch_taken,branch_condition;
    logic [31:0] wb_data;

    decoder u_decoder(.instruction(ir),.rs1_addr(rs1_addr),.rs2_addr(rs2_addr),.rd_addr(rd_addr),
        .instr_class(instr_class),.alu_op(alu_op),.imm_sel(imm_sel),
        .alu_src_a(alu_src_a),.alu_src_b(alu_src_b),.branch_op(branch_op),
        .mem_size(mem_size),.load_unsigned(load_unsigned),.rd_write(rd_write),
        .wb_sel(wb_sel),.illegal(decode_illegal));
    // Decoder recognizes more instructions than this initial top executes.
    assign core_illegal=decode_illegal ||
        !((instr_class==IC_ALU) || (instr_class==IC_FENCE) ||
          (instr_class==IC_ECALL) || (instr_class==IC_EBREAK) ||
          (instr_class==IC_BRANCH) || (instr_class==IC_JAL) || (instr_class==IC_JALR));

    control_fsm u_control(.clk(clk),.rst(rst),.instr_class(instr_class),
        .illegal(core_illegal),.rd_write(rd_write),.mem_size(mem_size),
        .pc(pc),.instr_pc(instr_pc),.mem_addr(aluout),.target_addr(aluout),.branch_taken(branch_taken),
        .imem_req_valid(imem_req_valid),.imem_req_ready(imem_req_ready),.imem_req_addr(imem_req_addr),
        .imem_rsp_valid(imem_rsp_valid),.imem_rsp_err(imem_rsp_err),.imem_rsp_ready(imem_rsp_ready),
        .dmem_req_valid(dmem_req_valid),.dmem_req_ready(dmem_req_ready),
        .dmem_req_write(dmem_req_write),.dmem_req_addr(dmem_req_addr),
        .dmem_rsp_valid(dmem_rsp_valid),.dmem_rsp_err(dmem_rsp_err),.dmem_rsp_ready(dmem_rsp_ready),
        .ir_we(ir_we),.instr_pc_we(instr_pc_we),.ab_we(ab_we),.aluout_we(aluout_we),
        .branch_taken_we(branch_taken_we),.mdr_we(mdr_we),.reg_we(reg_we),.pc_we(pc_we),
        .pc_sel(pc_sel),.instr_done(instr_done),.state(state),.mem_pending(mem_pending),
        .halted(halted),.halt_cause(halt_cause),.fault_pc(fault_pc),.fault_addr(fault_addr));
    regfile u_regfile(.clk(clk),.rst(rst),.rs1_addr(rs1_addr),.rs2_addr(rs2_addr),
        .rs1_data(rs1_data),.rs2_data(rs2_data),.rd_we(reg_we),.rd_addr(rd_addr),.rd_data(wb_data));
    imm_gen u_imm(.instruction(ir),.imm_sel(imm_sel),.imm(imm));
    alu u_alu(.a(alu_a),.b(alu_b),.alu_op(alu_op),.result(alu_result));
    pc_reg u_pc(.clk(clk),.rst(rst),.pc_we(pc_we),.pc_next(pc_next),.pc(pc));

    branch_compare u_branch(.a(a_reg),.b(b_reg),.branch_op(branch_op),.taken(branch_condition));
    assign wb_data=(wb_sel==WB_PC4)?(instr_pc+32'd4):aluout;
    always_comb begin
        case (alu_src_a)
            ALU_A_REG: alu_a=a_reg;
            ALU_A_PC: alu_a=instr_pc;
            default: alu_a=32'b0;
        endcase
        alu_b=(alu_src_b==ALU_B_REG)?b_reg:imm;
        pc_next=instr_pc+32'd4;
        if (pc_sel==PC_TARGET) pc_next=aluout;
    end
    always_ff @(posedge clk) begin
        if (rst) begin ir<=0; instr_pc<=0; a_reg<=0; b_reg<=0; aluout<=0; branch_taken<=0; end
        else begin
            if (ir_we) ir<=imem_rsp_data;
            if (instr_pc_we) instr_pc<=pc;
            if (ab_we) begin a_reg<=rs1_data; b_reg<=rs2_data; end
            if (aluout_we) begin
                if (instr_class==IC_JALR) aluout<={alu_result[31:1],1'b0};
                else aluout<=alu_result;
            end
            if (branch_taken_we) branch_taken<=branch_condition;
        end
    end
    assign dmem_req_wdata=32'b0;
    assign dmem_req_wstrb=4'b0;
    assign retire_valid=instr_done;
    assign retire_pc=instr_pc;
    assign retire_instruction=ir;
    assign retire_rd_we=instr_done && reg_we && (rd_addr!=0);
    assign retire_rd_addr=retire_rd_we?rd_addr:5'b0;
    assign retire_rd_data=retire_rd_we?wb_data:32'b0;
endmodule

```

## ⑦ 迴圈與函式呼叫：程式、位址與預期值

```asm
.section .text
.globl _start
_start:
    addi x1,x0,5
    addi x2,x0,0
    addi x3,x0,0
loop:
    addi x2,x2,1
    add x3,x3,x2
    blt x2,x1,loop
    jal x1,function
    jal x0,done
function:
    addi x3,x3,10
    jalr x0,0(x1)
done:
    ebreak
```

| PC | 指令 | 機器碼 | 作用 |
| --- | --- | --- | --- |
| `0x00` | `addi x1,x0,5` | `00500093` | 次數上限＝5 |
| `0x04` | `addi x2,x0,0` | `00000113` | 計數器＝0 |
| `0x08` | `addi x3,x0,0` | `00000193` | 總和＝0 |
| `0x0C` | `addi x2,x2,1` | `00110113` | 計數器＋1 |
| `0x10` | `add x3,x3,x2` | `002181B3` | 總和＋計數器 |
| `0x14` | `blt x2,x1,loop` | `FE114CE3` | 小於 5 時跳回 0x0C |
| `0x18` | `jal x1,function` | `008000EF` | x1＝0x1C，跳至 0x20 |
| `0x1C` | `jal x0,done` | `00C0006F` | 不寫 x0，跳至 0x28 |
| `0x20` | `addi x3,x3,10` | `00A18193` | 總和＋10 |
| `0x24` | `jalr x0,0(x1)` | `00008067` | 跳回 x1＝0x1C |
| `0x28` | `ebreak` | `00100073` | 停止 |

| 預期項目 | 值 |
| --- | --- |
| 迴圈五輪的 x3 | 1、3、6、10、15 |
| 函式執行後 x3 | 25＝0x00000019 |
| 最終 x2 | 5 |
| 最終 x1 | 0x0000001C |
| 正常 commit 數 | 22；包含五次 Branch、呼叫、返回及跳過函式的 JAL |
| 取指數 | 23，包含最後 EBREAK |
| 停止資訊 | PC／fault_pc＝0x28，cause＝HALT_EBREAK＝9，fault_addr＝0 |

### 巢狀呼叫

```asm
.section .text
.globl _start
_start:
    jal x1,outer
    jal x0,done
outer:
    addi x5,x1,0
    jal x1,inner
    addi x10,x10,2
    jalr x0,0(x5)
inner:
    addi x10,x10,3
    jalr x0,0(x1)
done:
    ebreak
```

外層函式用 x5 保存呼叫它的返回位址 0x04，內層呼叫把 x1 更新為 0x10。內層返回至 0x10，外層再用 x5 返回至 0x04。預期最終 x10＝5、x5＝4、x1＝0x10，8 次正常 commit，EBREAK 位於 0x20。

這是沒有記憶體的測試範例，直接用另一個 register 保存返回位址；一般函式 ABI 的 stack 保存／還原要等 Load／Store 接入後再驗證。

## ⑧ Testbench 與預期模型

| 檢查項目 | 驗收條件 |
| --- | --- |
| 六種 Branch | 成立與不成立皆與預期路徑一致，包含負數、相等及 signed 極值 |
| 分支目標 | 正向、反向及位移邊界，依 InstrPC 計算 |
| JAL | 正向／負向跳躍、x0、link 與對齊行為正確 |
| JALR | 正／負立即數、立即數邊界、bit 0 清除、rd＝rs1、rd＝x0 正確 |
| Commit | 每次 InstrPC、機器碼、目的暫存器、寫回值與下一個 PC 符合預期 |
| 未完成指令 | PC 保持，請求在 backpressure 下保持位址及 valid |
| 錯誤 | 未對齊指令不 commit、不寫 link；目標取指失敗保存已寫 link |
| Reset | Branch／Jump commit 前 reset，再由起點重跑完整程式 |
| 回歸 | 整數程式、非法指令、ECALL 與取指失敗行為正確 |
| 最終狀態 | 全部 32 個實際暫存器符合獨立預期值，停止後保持不執行 |

`build_cases.py` 使用軟體的指令語意模型，由指令運算元和 label 計算預期 trace 與最終暫存器，**不讀 DUT 訊號或複製 FSM 的 cycle 動作**。編碼器另產生機器碼送到硬體；原整數程式維持既有固定常數預期值。這個模型只涵蓋測試使用的指令，不是完整 RISC-V simulator，也不是正式 ISA compliance 認證。

`cases_init.svh` 包含全部測試指令與預期表；`cases.json` 可用來查閱完整程式、逐次 trace 與最終暫存器。testbench 不會用 trace 寫入或修改 DUT 的暫存器，只在停止時讀取它們驗證。

### 完整 testbench

```systemverilog
module tb_branch_cpu;
    timeunit 1ns;
    timeprecision 1ps;
    import fault_v_pkg::*;
    logic clk=0,rst;
    always #5 clk=~clk;
    logic imem_req_valid,imem_req_ready,imem_rsp_valid,imem_rsp_err,imem_rsp_ready;
    logic [31:0] imem_req_addr,imem_rsp_data;
    logic dmem_req_valid,dmem_req_ready,dmem_req_write,dmem_rsp_valid,dmem_rsp_err,dmem_rsp_ready;
    logic [31:0] dmem_req_addr,dmem_req_wdata,dmem_rsp_data;
    logic [3:0] dmem_req_wstrb;
    logic halted;
    halt_cause_t halt_cause;
    logic [31:0] fault_pc,fault_addr,pc;
    cpu_state_t state;
    logic retire_valid,retire_rd_we;
    logic [31:0] retire_pc,retire_instruction,retire_rd_data;
    logic [4:0] retire_rd_addr;
    fault_v_cpu dut(.*);
    logic [31:0] program_words[0:63],expected_value[0:255],expected_regs[0:31],golden_regs[0:31];
    logic [4:0] expected_rd[0:255];
    integer program_len,expected_commits,retired,requests,cycles,scenarios=0;
    integer mode,error_index,request_timer,response_timer,accepted_index,j;
    logic busy,stalled;
    logic [31:0] expected_pc[0:255],expected_inst[0:255],expected_next[0:255],previous_next;
    string case_name;
    halt_cause_t expected_cause;
    logic [31:0] expected_fault_pc,expected_fault_addr;
    integer case_id,delay_mode;
    logic [31:0] stalled_addr,previous_pc;
    logic previous_commit;

    task automatic must(input logic condition,input string label_text);
        if (condition !== 1'b1)
            $fatal(1,"FAIL %s state=%0d pc=%h retired=%0d",label_text,state,pc,retired);
    endtask
    task automatic tick; @(posedge clk); #1; endtask
    task automatic load_case(input integer case_id);
        for (integer k=0;k<64;k=k+1) program_words[k]=0;
        `include "cases_init.svh"
    endtask
    task automatic reset_core;
        @(negedge clk); rst=1;
        tick; @(negedge clk); rst=0;
    endtask

    // Instruction memory stand-in: one accepted request, held response.
    always @(posedge clk) begin
        if (rst) begin
            imem_req_ready<=0; imem_rsp_valid<=0; imem_rsp_err<=0; imem_rsp_data<=0;
            busy<=0; request_timer<=0; response_timer<=0; accepted_index<=0; requests<=0;
        end else begin
            if (!busy) begin
                if (imem_req_valid && !imem_req_ready) begin
                    if (request_timer>=((mode==0)?0:(requests%4))) imem_req_ready<=1;
                    else request_timer<=request_timer+1;
                end
                if (imem_req_valid && imem_req_ready) begin
                    busy<=1; imem_req_ready<=0; requests<=requests+1;
                    accepted_index<=imem_req_addr[31:2];
                    response_timer<=(mode==0)?0:((requests+mode)%5);
                end
            end else if (!imem_rsp_valid) begin
                if (response_timer==0) begin
                    imem_rsp_valid<=1;
                    imem_rsp_err<=((accepted_index==error_index) || (accepted_index>=program_len));
                    if (accepted_index<program_len) imem_rsp_data<=program_words[accepted_index];
                    else imem_rsp_data<=0;
                end else response_timer<=response_timer-1;
            end
            if (imem_rsp_valid && imem_rsp_ready) begin
                imem_rsp_valid<=0; busy<=0; request_timer<=0;
            end
        end
    end

    // Commit trace is sampled before the same edge changes PC and RF.
    always @(posedge clk) begin
        if (rst) begin
            retired=0; stalled=0; previous_pc=0; previous_commit=0;
            for (integer r=0;r<32;r=r+1) expected_regs[r]=0;
        end else begin
            must(!dmem_req_valid && !dmem_rsp_ready,"unimplemented data path remains inactive");
            if (stalled) must(imem_req_valid && imem_req_addr==stalled_addr,"request stable during backpressure");
            if (!previous_commit) must(pc==previous_pc,"PC held until commit");
            else must(pc===previous_next,"committed next PC");
            if (retire_valid) begin
                must(retired<expected_commits,"no extra commits");
                must(retire_pc===expected_pc[retired],"instruction PC");
                must(retire_instruction===expected_inst[retired],"executed requested instruction");
                must(retire_rd_we== (expected_rd[retired]!=0),"write enable including x0");
                must(retire_rd_addr===expected_rd[retired] && retire_rd_data===expected_value[retired],"destination and result");
                if (expected_rd[retired]!=0) expected_regs[expected_rd[retired]]=expected_value[retired];
                previous_next=expected_next[retired];
                retired=retired+1;
            end
            stalled=imem_req_valid && !imem_req_ready; stalled_addr=imem_req_addr;
            previous_pc=pc; previous_commit=retire_valid;
        end
    end

    task automatic await_halt(input string label_text,input halt_cause_t cause,
                              input logic [31:0] expected_fault_pc,expected_fault_addr);
        cycles=0;
        while (!halted) begin
            tick; cycles=cycles+1;
            if (cycles>3000) $fatal(1,"TIMEOUT %s",label_text);
        end
        must(retired==expected_commits,"all expected instructions committed");
        must(halt_cause==cause && fault_pc==expected_fault_pc && fault_addr==expected_fault_addr,"termination cause/context");
        must(pc==expected_fault_pc,"stopped PC");
        must(requests==expected_commits+1,"one fetch per instruction including stop");
        for (integer r=0;r<32;r=r+1)
            begin
                must(dut.u_regfile.regs[r]===golden_regs[r],"final register file matches independent model");
                must(expected_regs[r]===golden_regs[r],"commit trace matches independent final state");
            end
        repeat(4) tick;
        must(!imem_req_valid && !retire_valid && retired==expected_commits,"halt remains inactive");
        scenarios=scenarios+1;
        $display("PASS %0d: %s committed=%0d requests=%0d pc=%h cause=%0d",scenarios,label_text,retired,requests,pc,halt_cause);
    endtask

    initial begin
        rst=1; mode=0; error_index=-1;
        dmem_req_ready=0; dmem_rsp_valid=0; dmem_rsp_err=0; dmem_rsp_data=0;
        for (case_id=0;case_id<66;case_id=case_id+1) begin
            for (delay_mode=0;delay_mode<2;delay_mode=delay_mode+1) begin
                @(negedge clk); rst=1; mode=delay_mode*2; load_case(case_id);
                tick; @(negedge clk); rst=0;
                await_halt(case_name,expected_cause,expected_fault_pc,expected_fault_addr);
            end
        end
        // Cancel execution immediately before a branch or jump commit, then restart.
        for (integer k=0;k<2;k=k+1) begin
            @(negedge clk); rst=1; mode=2; load_case(37);
            tick; @(negedge clk); rst=0;
            cycles=0;
            while (state!=((k==0)?ST_BR_COMMIT:ST_JUMP_COMMIT)) begin
                tick; cycles=cycles+1;
                if (cycles>3000) $fatal(1,"reset setup timeout");
            end
            reset_core;
            await_halt("reset before control-flow commit then restart",expected_cause,expected_fault_pc,expected_fault_addr);
        end
        $display("ALL %0d BRANCH CPU SCENARIOS PASSED",scenarios);
        $finish;
    end
    initial begin #1000000; $fatal(1,"GLOBAL TIMEOUT tb_branch_cpu"); end
endmodule
```

### 所有程式的預期結果

每個程式分別以基本延遲和可變等待執行一次。下表的編號是 `load_case` 使用的 case_id。cause：1＝非法指令，2＝指令目標未對齊，3＝取指失敗，8＝ECALL，9＝EBREAK。

| case_id | 程式 | 正常 commit | 停止 PC | cause | fault_addr |
| --- | --- | --- | --- | --- | --- |
| 0 | integer instruction regression | 37 | `00000094` | 9 | `00000000` |
| 1 | beq a=ffffffff b=00000001 | 5 | `00000014` | 9 | `00000000` |
| 2 | beq a=00000001 b=ffffffff | 5 | `00000014` | 9 | `00000000` |
| 3 | beq a=00000007 b=00000007 | 4 | `00000014` | 9 | `00000000` |
| 4 | beq a=80000000 b=7fffffff | 7 | `0000001C` | 9 | `00000000` |
| 5 | beq taken target misaligned | 2 | `00000008` | 2 | `0000000A` |
| 6 | beq not taken target misaligned | 4 | `00000010` | 9 | `00000000` |
| 7 | bne a=ffffffff b=00000001 | 4 | `00000014` | 9 | `00000000` |
| 8 | bne a=00000001 b=ffffffff | 4 | `00000014` | 9 | `00000000` |
| 9 | bne a=00000007 b=00000007 | 5 | `00000014` | 9 | `00000000` |
| 10 | bne a=80000000 b=7fffffff | 6 | `0000001C` | 9 | `00000000` |
| 11 | bne taken target misaligned | 2 | `00000008` | 2 | `0000000A` |
| 12 | bne not taken target misaligned | 4 | `00000010` | 9 | `00000000` |
| 13 | blt a=ffffffff b=00000001 | 4 | `00000014` | 9 | `00000000` |
| 14 | blt a=00000001 b=ffffffff | 5 | `00000014` | 9 | `00000000` |
| 15 | blt a=00000007 b=00000007 | 5 | `00000014` | 9 | `00000000` |
| 16 | blt a=80000000 b=7fffffff | 6 | `0000001C` | 9 | `00000000` |
| 17 | blt taken target misaligned | 2 | `00000008` | 2 | `0000000A` |
| 18 | blt not taken target misaligned | 4 | `00000010` | 9 | `00000000` |
| 19 | bge a=ffffffff b=00000001 | 5 | `00000014` | 9 | `00000000` |
| 20 | bge a=00000001 b=ffffffff | 4 | `00000014` | 9 | `00000000` |
| 21 | bge a=00000007 b=00000007 | 4 | `00000014` | 9 | `00000000` |
| 22 | bge a=80000000 b=7fffffff | 7 | `0000001C` | 9 | `00000000` |
| 23 | bge taken target misaligned | 2 | `00000008` | 2 | `0000000A` |
| 24 | bge not taken target misaligned | 4 | `00000010` | 9 | `00000000` |
| 25 | bltu a=ffffffff b=00000001 | 5 | `00000014` | 9 | `00000000` |
| 26 | bltu a=00000001 b=ffffffff | 4 | `00000014` | 9 | `00000000` |
| 27 | bltu a=00000007 b=00000007 | 5 | `00000014` | 9 | `00000000` |
| 28 | bltu a=80000000 b=7fffffff | 7 | `0000001C` | 9 | `00000000` |
| 29 | bltu taken target misaligned | 2 | `00000008` | 2 | `0000000A` |
| 30 | bltu not taken target misaligned | 4 | `00000010` | 9 | `00000000` |
| 31 | bgeu a=ffffffff b=00000001 | 4 | `00000014` | 9 | `00000000` |
| 32 | bgeu a=00000001 b=ffffffff | 5 | `00000014` | 9 | `00000000` |
| 33 | bgeu a=00000007 b=00000007 | 4 | `00000014` | 9 | `00000000` |
| 34 | bgeu a=80000000 b=7fffffff | 6 | `0000001C` | 9 | `00000000` |
| 35 | bgeu taken target misaligned | 2 | `00000008` | 2 | `0000000A` |
| 36 | bgeu not taken target misaligned | 4 | `00000010` | 9 | `00000000` |
| 37 | backward loop and function return | 22 | `00000028` | 9 | `00000000` |
| 38 | nested calls preserving outer return register | 8 | `00000020` | 9 | `00000000` |
| 39 | JALR clears odd bit zero | 3 | `00000014` | 9 | `00000000` |
| 40 | JALR negative offset | 3 | `00000014` | 9 | `00000000` |
| 41 | JALR rd equals rs1 | 3 | `00000014` | 9 | `00000000` |
| 42 | JALR rd x0 | 3 | `00000014` | 9 | `00000000` |
| 43 | JALR offset bit zero | 3 | `00000014` | 9 | `00000000` |
| 44 | JALR clears bit0 but bit1 remains | 1 | `00000004` | 2 | `00000012` |
| 45 | JALR high aligned address fetch fails | 2 | `FFFFFFFC` | 3 | `FFFFFFFC` |
| 46 | JALR maximum positive immediate | 2 | `00000800` | 3 | `00000800` |
| 47 | JALR minimum negative immediate | 4 | `00000014` | 9 | `00000000` |
| 48 | JAL misaligned keeps link | 1 | `00000004` | 2 | `00000006` |
| 49 | JAL x0 skips instruction | 2 | `0000000C` | 9 | `00000000` |
| 50 | JAL high target fetch fails | 1 | `FFFFFFFC` | 3 | `FFFFFFFC` |
| 51 | JAL negative offset within program | 4 | `00000010` | 9 | `00000000` |
| 52 | branch displacement boundary 4092 | 1 | `00000FFC` | 3 | `00000FFC` |
| 53 | branch displacement boundary 4094 | 0 | `00000000` | 2 | `00000FFE` |
| 54 | branch displacement boundary -4096 | 1 | `FFFFF000` | 3 | `FFFFF000` |
| 55 | JAL displacement boundary 1048572 | 1 | `000FFFFC` | 3 | `000FFFFC` |
| 56 | JAL displacement boundary 1048574 | 0 | `00000000` | 2 | `000FFFFE` |
| 57 | JAL displacement boundary -1048576 | 1 | `FFF00000` | 3 | `FFF00000` |
| 58 | load remains unsupported | 1 | `00000004` | 1 | `00000000` |
| 59 | store remains unsupported | 1 | `00000004` | 1 | `00000000` |
| 60 | MUL illegal | 1 | `00000004` | 1 | `00000000` |
| 61 | reserved branch funct3 illegal | 1 | `00000004` | 1 | `00000000` |
| 62 | JALR nonzero funct3 illegal | 1 | `00000004` | 1 | `00000000` |
| 63 | jump target fetch error preserves link | 1 | `00000008` | 3 | `00000008` |
| 64 | ECALL regression | 1 | `00000004` | 8 | `00000000` |
| 65 | sequential fetch error regression | 1 | `00000004` | 3 | `00000004` |

另有兩次在 BR_COMMIT／JUMP_COMMIT 前 reset，再重跑迴圈程式的情境。reset 前取消的指令不算進重啟後的 commit 次數。

預期最後輸出：

```text
PASS 133: reset before control-flow commit then restart committed=22 requests=23 pc=00000028 cause=9
PASS 134: reset before control-flow commit then restart committed=22 requests=23 pc=00000028 cause=9
ALL 134 BRANCH CPU SCENARIOS PASSED
```

測試記憶體有 64 words，支援單筆取指交易，不是最終 16 KiB 的記憶體實作。大位移跳躍落在這個範圍外，模型故意回應存取失敗；這可以驗證跳躍已完成後的取指錯誤。模型沒有把「超出範圍」當成 CPU 對齊錯誤。

## ⑨ Vivado 使用方式

1. 解壓縮檔案包到一般本機資料夾。
2. Design Sources 加入 `rtl` 內九個 `.sv`。使用本包完整版本，避免同時加入舊 top、重複 package 或同名 module。
3. Simulation Sources 加入 `verify/tb_branch_cpu.sv` 與 `verify/cases_init.svh`。若找不到 include，將 `verify` 完整路徑加入 Simulation Include Directories。
4. Simulation Top 設成 **tb_branch_cpu**；Design Top 則是 **fault_v_cpu**。
5. 執行 Behavioral Simulation，Tcl Console 輸入 **run all**。1000 ns 不足以跑完全部情境。
6. 確認最後的 `ALL 134 BRANCH CPU SCENARIOS PASSED` 與正常 `$finish`，沒有 Fatal。

不需要先刪除 ALU、imm_gen 或 Register File；這些都是 top 的必要模組。舊 testbench 可留著，但本次要選對 Simulation Top。`.mem` 只是參考程式檔，本次 testbench 使用 `.svh` 初始化，不額外執行 `$readmemh`。

也可用 PowerShell 執行 `run_xsim.ps1`；預設 Vivado 2022.2 路徑，可用 `-VivadoBin` 指定其他安裝路徑。Python 只在重新產生測試資料時需要，直接執行既有 XSim 測試不需要 Python。

| 檔案 | 用途 |
| --- | --- |
| rtl/fault_v_cpu.sv | 加入 Branch／Jump 的 CPU top |
| rtl/branch_compare.sv | 組合比較器 |
| rtl 其他七檔 | package、FSM、Decoder、ALU、imm_gen、RegFile、PC |
| verify/tb_branch_cpu.sv | 取指模型、測試驅動與檢查 |
| verify/cases_init.svh | 完整機器碼／預期結果表 |
| verify/loop_call.S／nested_call.S | 可閱讀的範例程式 |
| verify/program_37.mem／program_38.mem | 迴圈／巢狀呼叫的逐行機器碼 |
| cases.json／build_cases.py | 預期結果與可重產生的指令語意模型 |
| reference_inputs | 重產生整數回歸資料所需的固定來源；不是本次 Simulation Sources |
| run_xsim.ps1 | 編譯、elaboration、模擬及 PASS 檢查 |
| logs/branch_cpu_results.log | 獨立模擬紀錄 |

模擬的 10 ns clock 是測試用時間步進，不代表已達成 FPGA／ASIC 100 MHz 時序。此處驗收功能行為；綜合、時序及實板驗證需要各自的證據。
