# Fault-V：整數指令 CPU Datapath

## ① 模組用途與範圍

`fault_v_cpu` 把 Decoder、Immediate Generator、Register File、ALU、PC 與 Control FSM 接成實際硬體資料路徑。Testbench 只提供時脈、reset、指令記憶體回應與檢查結果；CPU 內部的指令、運算元、寫回及 PC 更新皆由 RTL 控制。

| 項目 | 規格 |
| --- | --- |
| 資料寬度 | 32-bit |
| 微架構 | 多周期、一次執行一條指令、FSM 控制 |
| 指令長度 | 固定 32-bit，順序位址加 4 |
| Register File | 32×32-bit，兩讀一寫，x0 固定為 0 |
| Reset | 高有效、同步 reset；PC 與內部暫存器清為 0 |
| 核心可執行範圍 | 21 種整數運算指令，以及 FENCE、ECALL、EBREAK 的既定行為 |
| 記憶體交易 | 指令請求／回應握手，一次最多一筆；允許等待 |
| 資料介面 | 保留接腳，尚未連接 Load／Store 資料路徑 |
| 錯誤處理 | 停止、保存原因與位址，直到 reset |
| 使用環境 | 裸機；沒有標準 trap／CSR／中斷 |

**Decoder 能辨識的指令比這個 top 能執行的指令多。這個 top 是 RV32I 整數運算子集，不能宣稱已完成完整 RV32I CPU。**

| 指令類別 | 指令 | 行為 |
| --- | --- | --- |
| R-type，10 種 | ADD、SUB、AND、OR、XOR、SLL、SRL、SRA、SLT、SLTU | A 與 B 運算，結果寫回 rd |
| I-type 運算，9 種 | ADDI、ANDI、ORI、XORI、SLTI、SLTIU、SLLI、SRLI、SRAI | A 與立即數運算，結果寫回 rd |
| U-type，2 種 | LUI、AUIPC | 立即數，或 InstrPC＋立即數，寫回 rd |
| FENCE | FENCE | 無資料存取及寫入緩衝的本子集，依序完成後繼續 |
| 停止指令 | ECALL、EBREAK | 分別以 HALT_ECALL／HALT_EBREAK 停止，PC 不前進 |
| 尚未接入 | Branch、JAL／JALR、Load／Store | 即使 Decoder 認得，也以 HALT_ILLEGAL 停止 |
| 不支援擴充 | MUL、CSR、壓縮指令等 | 非法指令停止 |

加減法保留低 32-bit，不因整數溢位停止。SLT／SLTI 採 signed 比較；SLTU／SLTIU 採 unsigned 比較，但 SLTIU 的立即數仍先做符號擴展。所有移位只使用第二運算元的低 5-bit。SRA／SRAI 複製符號位。

## ② Datapath 架構

```text
PC → 指令請求介面 → 指令回應資料 → IR → Decoder
 │                                  ├→ rs1／rs2／rd 編號
 └→ InstrPC（取指成功時保存 PC）      ├→ ALU 與 MUX 控制
                                    └→ imm_sel → imm_gen → imm

rs1／rs2 → Register File → A／B 暫存器

A／InstrPC／0 → ALU 左輸入 MUX ┐
B／imm       → ALU 右輸入 MUX ├→ ALU → ALUOut → Register File rd
                              ┘
InstrPC + 4 → PC next → PC（正常完成時更新）

Control FSM → 各暫存器 enable、記憶體握手、錯誤停止及 commit trace
```

| 保存位置 | 寬度 | 更新條件 | 用途 |
| --- | --- | --- | --- |
| PC | 32-bit | reset 或 pc_we | 下一次取指位址；執行與等待期間保持 |
| IR | 32-bit | ir_we | 取指成功的完整指令 |
| InstrPC | 32-bit | instr_pc_we，與 IR 同時 | 目前指令所在位址，供 AUIPC 與下一個 PC 計算 |
| A、B | 各 32-bit | ab_we | Decode 階段保存兩個讀取埠資料 |
| ALUOut | 32-bit | aluout_we | Execute 階段保存運算結果，供下一拍寫回 |
| Register File | 32×32-bit | reg_we，上升緣寫入 | 架構暫存器；rd＝0 的寫入忽略 |
| State／pending／錯誤資訊 | 依既有 controller 定義 | FSM 內部控制 | 保存狀態、交易及停止資訊 |

| 指令 | ALU A | ALU B | 寫回資料 |
| --- | --- | --- | --- |
| R-type | A | B | ALUOut |
| I-type 運算 | A | imm | ALUOut |
| LUI | 0 | U-type imm | ALUOut＝imm |
| AUIPC | InstrPC | U-type imm | ALUOut＝InstrPC＋imm |

`ALU_A_PC` 在這裡代表 **InstrPC**。同一條指令使用的 IR、InstrPC、A、B 在運算及寫回期间保持；不能拿已前進的 PC 計算 AUIPC。

## ③ 狀態與更新時機

| 狀態 | 動作 | 上升緣更新 |
| --- | --- | --- |
| FETCH：尚未接受請求 | 保持 imem_req_valid 與位址，等待 req_ready | 接受請求後保存 pending |
| FETCH：請求已接受 | 不重複送請求，等待有效回應 | 成功回應時更新 IR、InstrPC，進入 DECODE |
| DECODE | 解碼，檢查非法指令或 top 未接入的指令類別 | 一般整數指令保存 A／B，進入 ALU_EXEC |
| ALU_EXEC | MUX 選輸入，ALU 做對應運算 | ALUOut 保存結果，進入 ALU_WB |
| ALU_WB | 開啟 reg_we、pc_we、instr_done | 寫回 rd，PC＝InstrPC＋4，回到 FETCH |
| FENCE_COMMIT | 不寫 rd，開啟 pc_we、instr_done | PC＝InstrPC＋4，回到 FETCH |
| HALTED | 不發起請求、不寫回、不更新 PC | 保存停止狀態直到 reset |

順序相依指令不需要 forwarding：前一條指令完成寫回後，才取下一條指令。若 rd 與 rs1 相同，A 在 Decode 已保存舊值，之後寫回新值，不會破壞該次運算。

本測試的取指記憶體會先接受請求，再於後續時脈回應；不能把同一個 edge 的首次 request acceptance 當成 response acceptance。回應必須保持到 rsp_valid 且 rsp_ready 的上升緣。

## ④ Top 模組介面

| 訊號 | 方向 | 寬度 | 定義 |
| --- | --- | --- | --- |
| clk／rst | 輸入 | 各 1 | 單一 clock、高有效同步 reset |
| imem_req_valid／imem_req_ready | 輸出／輸入 | 各 1 | 取指請求握手 |
| imem_req_addr | 輸出 | 32 | Byte address；正常取指對齊 4 bytes |
| imem_rsp_valid／imem_rsp_ready | 輸入／輸出 | 各 1 | 取指回應握手 |
| imem_rsp_data／imem_rsp_err | 輸入 | 32／1 | 指令資料／存取失敗 |
| dmem_req_valid／dmem_req_ready | 輸出／輸入 | 各 1 | 保留資料請求介面；本 top 不發交易 |
| dmem_req_write／dmem_req_addr | 輸出 | 1／32 | 資料讀寫方向／位址 |
| dmem_req_wdata／dmem_req_wstrb | 輸出 | 32／4 | 本版固定 0，尚未接 Store 格式化 |
| dmem_rsp_valid／dmem_rsp_err／dmem_rsp_data | 輸入 | 1／1／32 | 保留資料回應介面 |
| dmem_rsp_ready | 輸出 | 1 | 本子集保持 0 |
| halted／halt_cause | 輸出 | 1／4 | 停止狀態與原因 |
| fault_pc／fault_addr | 輸出 | 各 32 | 錯誤上下文；依原因定義 |
| pc／state | 輸出 | 32／4 | 除錯觀察訊號 |

### Commit 觀察介面

| 訊號 | 寬度 | 定義 |
| --- | --- | --- |
| retire_valid | 1 | 該上升緣正常完成一條指令 |
| retire_pc／retire_instruction | 各 32 | 完成指令的位址／機器碼 |
| retire_rd_we | 1 | 該指令真的寫入 x1～x31；寫 x0 或 FENCE 為 0 |
| retire_rd_addr／retire_rd_data | 5／32 | 寫入編號／值；未寫入時輸出 0 |

這些是組合輸出，應在完成指令的 **clock 上升緣、非阻塞更新之前**取樣。若等待 PC／State 更新後才讀，訊號可能已變成下一個狀態。這是專案自訂 trace，並非完整 RVFI。停止或錯誤的指令不產生正常 retire_valid。

## ⑤ 完整 CPU Top RTL

既有 `fault_v_pkg.sv`、`control_fsm.sv`、`decoder.sv`、`alu.sv`、`imm_gen.sv`、`regfile.sv`、`pc_reg.sv` 應與下面的 top 一起使用。檔案包包含相同介面版本，不要同時匯入重複的 package 或同名 module。

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
    // Reserved for the subsequent branch/load/store integration.
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
    logic instr_done,mem_pending;

    decoder u_decoder(.instruction(ir),.rs1_addr(rs1_addr),.rs2_addr(rs2_addr),.rd_addr(rd_addr),
        .instr_class(instr_class),.alu_op(alu_op),.imm_sel(imm_sel),
        .alu_src_a(alu_src_a),.alu_src_b(alu_src_b),.branch_op(branch_op),
        .mem_size(mem_size),.load_unsigned(load_unsigned),.rd_write(rd_write),
        .wb_sel(wb_sel),.illegal(decode_illegal));
    // Decoder recognizes more instructions than this initial top executes.
    assign core_illegal=decode_illegal ||
        !((instr_class==IC_ALU) || (instr_class==IC_FENCE) ||
          (instr_class==IC_ECALL) || (instr_class==IC_EBREAK));

    control_fsm u_control(.clk(clk),.rst(rst),.instr_class(instr_class),
        .illegal(core_illegal),.rd_write(rd_write),.mem_size(mem_size),
        .pc(pc),.instr_pc(instr_pc),.mem_addr(aluout),.target_addr(aluout),.branch_taken(1'b0),
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
        .rs1_data(rs1_data),.rs2_data(rs2_data),.rd_we(reg_we),.rd_addr(rd_addr),.rd_data(aluout));
    imm_gen u_imm(.instruction(ir),.imm_sel(imm_sel),.imm(imm));
    alu u_alu(.a(alu_a),.b(alu_b),.alu_op(alu_op),.result(alu_result));
    pc_reg u_pc(.clk(clk),.rst(rst),.pc_we(pc_we),.pc_next(pc_next),.pc(pc));

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
        if (rst) begin ir<=0; instr_pc<=0; a_reg<=0; b_reg<=0; aluout<=0; end
        else begin
            if (ir_we) ir<=imem_rsp_data;
            if (instr_pc_we) instr_pc<=pc;
            if (ab_we) begin a_reg<=rs1_data; b_reg<=rs2_data; end
            if (aluout_we) aluout<=alu_result;
        end
    end
    assign dmem_req_wdata=32'b0;
    assign dmem_req_wstrb=4'b0;
    assign retire_valid=instr_done;
    assign retire_pc=instr_pc;
    assign retire_instruction=ir;
    assign retire_rd_we=instr_done && reg_we && (rd_addr!=0);
    assign retire_rd_addr=retire_rd_we?rd_addr:5'b0;
    assign retire_rd_data=retire_rd_we?aluout:32'b0;
endmodule
```

## ⑥ 程式與預期结果

下面是一段有前後資料相依的連續程式，不是逐條 reset 的單元測試。Byte address 從 0 開始，每條加 4。表中的結果是架構寫回值；x0／FENCE 不寫入，trace 資料為 0。

| PC | 指令 | 機器碼 | 寫回 | 預期值 |
| --- | --- | --- | --- | --- |
| `0x00000000` | `addi x1,x0,5` | `00500093` | x1 | `00000005` |
| `0x00000004` | `addi x2,x0,-3` | `FFD00113` | x2 | `FFFFFFFD` |
| `0x00000008` | `addi x3,x0,32` | `02000193` | x3 | `00000020` |
| `0x0000000C` | `addi x4,x0,31` | `01F00213` | x4 | `0000001F` |
| `0x00000010` | `addi x5,x0,1` | `00100293` | x5 | `00000001` |
| `0x00000014` | `add x6,x1,x2` | `00208333` | x6 | `00000002` |
| `0x00000018` | `sub x7,x2,x1` | `401103B3` | x7 | `FFFFFFF8` |
| `0x0000001C` | `and x8,x1,x2` | `0020F433` | x8 | `00000005` |
| `0x00000020` | `or x9,x1,x2` | `0020E4B3` | x9 | `FFFFFFFD` |
| `0x00000024` | `xor x10,x1,x2` | `0020C533` | x10 | `FFFFFFF8` |
| `0x00000028` | `slt x11,x2,x1` | `001125B3` | x11 | `00000001` |
| `0x0000002C` | `sltu x12,x2,x1` | `00113633` | x12 | `00000000` |
| `0x00000030` | `sll x13,x5,x4` | `004296B3` | x13 | `80000000` |
| `0x00000034` | `srl x14,x13,x5` | `0056D733` | x14 | `40000000` |
| `0x00000038` | `sra x15,x13,x5` | `4056D7B3` | x15 | `C0000000` |
| `0x0000003C` | `sll x16,x5,x3` | `00329833` | x16 | `00000001` |
| `0x00000040` | `addi x17,x1,-4` | `FFC08893` | x17 | `00000001` |
| `0x00000044` | `andi x18,x2,15` | `00F17913` | x18 | `0000000D` |
| `0x00000048` | `ori x19,x1,16` | `0100E993` | x19 | `00000015` |
| `0x0000004C` | `xori x20,x1,-1` | `FFF0CA13` | x20 | `FFFFFFFA` |
| `0x00000050` | `slti x21,x2,-1` | `FFF12A93` | x21 | `00000001` |
| `0x00000054` | `sltiu x22,x1,-1` | `FFF0BB13` | x22 | `00000001` |
| `0x00000058` | `slli x23,x5,31` | `01F29B93` | x23 | `80000000` |
| `0x0000005C` | `srli x24,x23,31` | `01FBDC13` | x24 | `00000001` |
| `0x00000060` | `srai x25,x23,31` | `41FBDC93` | x25 | `FFFFFFFF` |
| `0x00000064` | `lui x26,0x12345` | `12345D37` | x26 | `12345000` |
| `0x00000068` | `auipc x27,0x1` | `00001D97` | x27 | `00001068` |
| `0x0000006C` | `addi x26,x26,0x678` | `678D0D13` | x26 | `12345678` |
| `0x00000070` | `add x28,x6,x17` | `01130E33` | x28 | `00000003` |
| `0x00000074` | `addi x0,x0,99` | `06300013` | 不寫入 | `00000000` |
| `0x00000078` | `add x29,x0,x28` | `01C00EB3` | x29 | `00000003` |
| `0x0000007C` | `addi x30,x2,3` | `00310F13` | x30 | `00000000` |
| `0x00000080` | `lui x31,0x80000` | `80000FB7` | x31 | `80000000` |
| `0x00000084` | `addi x31,x31,-1` | `FFFF8F93` | x31 | `7FFFFFFF` |
| `0x00000088` | `addi x31,x31,1` | `001F8F93` | x31 | `80000000` |
| `0x0000008C` | `fence iorw,iorw` | `0FF0000F` | 不寫入 | `00000000` |
| `0x00000090` | `addi x0,x0,0` | `00000013` | 不寫入 | `00000000` |
| `0x00000094` | `ebreak` | `00100073` | 停止 | cause＝9、fault_pc＝0x94、fault_addr＝0 |

其中 `lui x31,0x80000` 先得到 `0x80000000`，再加 -1 得到 `0x7FFFFFFF`，最後加 1 得到 `0x80000000`，驗證加法只保留低 32-bit。AUIPC 位於 `0x68`，所以結果是 `0x68＋0x1000＝0x1068`。

## ⑦ 驗證設計與驗收條件

| 情境 | 驗證重點 | 預期結果 |
| --- | --- | --- |
| 相依整數程式，三組取指延遲 | 全部 21 種整數運算、FENCE、x0、同址讀寫、取指等待 | 各 37 次正常 commit、38 次取指，EBREAK 停於 0x94 |
| Load／Branch／Jump | top 範圍限制確實阻止未接入路徑 | 各在 PC＝4 以非法指令原因停止，不發資料交易 |
| MUL／非法 shift 編碼 | 未支援擴充與編碼檢查 | PC＝4、HALT_ILLEGAL |
| ECALL | 與 EBREAK 區分 | PC＝4、HALT_ECALL |
| 第二次取指失敗 | 保留已完成指令的寫回，保存失敗位址 | x1＝5，PC／fault_pc／fault_addr＝4、HALT_FETCH_ACCESS |
| 請求已接受時 reset，再重跑 | 核心與記憶體共同 reset，清掉舊回應 | 從 PC＝0 重新執行完整程式 |

每次正常 commit 都檢查指令、InstrPC、目的暫存器、寫入值；等待期間檢查 PC 保持與請求位址稳定。停止後比較全部 32 個實際暫存器與預期模型，並再等待四拍確認不繼續執行。程式測試涵蓋上述案例，沒有把有限案例當成所有輸入的完整證明。

測試記憶體只有 64 words，用來模擬本程式，**不是最終 16 KiB 記憶體實作**。reset 測試要求核心與記憶體一起清掉 pending／舊回應；若整合獨立外部記憶體，必須另訂 reset 期間的交易處理。

### Testbench：tb_fault_v_cpu.sv

```systemverilog
module tb_fault_v_cpu;
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
    logic [31:0] program_words[0:63],expected_value[0:63],expected_regs[0:31];
    logic [4:0] expected_rd[0:63];
    integer program_len,expected_commits,retired,requests,cycles,scenarios=0;
    integer mode,error_index,request_timer,response_timer,accepted_index,j;
    logic busy,stalled;
    logic [31:0] stalled_addr,previous_pc;
    logic previous_commit;

    task automatic must(input logic condition,input string label_text);
        if (condition !== 1'b1)
            $fatal(1,"FAIL %s state=%0d pc=%h retired=%0d",label_text,state,pc,retired);
    endtask
    task automatic tick; @(posedge clk); #1; endtask
    task automatic load_long_program;
        `include "program_init.svh"
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
            if (retire_valid) begin
                must(retired<expected_commits,"no extra commits");
                must(retire_pc==retired*4,"sequential instruction PC");
                must(retire_instruction===program_words[retired],"executed requested instruction");
                must(retire_rd_we== (expected_rd[retired]!=0),"write enable including x0");
                must(retire_rd_addr===expected_rd[retired] && retire_rd_data===expected_value[retired],"destination and result");
                if (expected_rd[retired]!=0) expected_regs[expected_rd[retired]]=expected_value[retired];
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
            must(dut.u_regfile.regs[r]===expected_regs[r],"final register file matches golden trace");
        repeat(4) tick;
        must(!imem_req_valid && !retire_valid && retired==expected_commits,"halt remains inactive");
        scenarios=scenarios+1;
        $display("PASS %0d: %s committed=%0d requests=%0d pc=%h cause=%0d",scenarios,label_text,retired,requests,pc,halt_cause);
    endtask

    task automatic short_fault(input string label_text,input logic [31:0] second,
                               input halt_cause_t cause,input logic fetch_error);
        @(negedge clk); rst=1;
        program_words[0]=32'h00500093; expected_rd[0]=1; expected_value[0]=5;
        program_words[1]=second; program_len=2; expected_commits=1;
        mode=2; error_index=fetch_error?1:-1;
        tick; @(negedge clk); rst=0;
        await_halt(label_text,cause,4,fetch_error?4:0);
    endtask

    initial begin
        rst=1; mode=0; error_index=-1;
        dmem_req_ready=0; dmem_rsp_valid=0; dmem_rsp_err=0; dmem_rsp_data=0;
        for (j=0;j<64;j=j+1) begin program_words[j]=0; expected_rd[j]=0; expected_value[j]=0; end
        for (j=0;j<3;j=j+1) begin
            @(negedge clk); rst=1; mode=j; error_index=-1; load_long_program;
            tick; @(negedge clk); rst=0;
            await_halt("dependent integer program",HALT_EBREAK,expected_commits*4,0);
        end
        short_fault("load not yet supported",32'h00002083,HALT_ILLEGAL,0);
        short_fault("branch not yet supported",32'h00000063,HALT_ILLEGAL,0);
        short_fault("jump not yet supported",32'h0000006f,HALT_ILLEGAL,0);
        short_fault("MUL not supported",32'h027302b3,HALT_ILLEGAL,0);
        short_fault("illegal shift encoding",32'h02009093,HALT_ILLEGAL,0);
        short_fault("ECALL stops with own cause",32'h00000073,HALT_ECALL,0);
        short_fault("fetch failure preserves prior write",32'h00100073,HALT_FETCH_ACCESS,1);

        @(negedge clk); rst=1; mode=2; error_index=-1; load_long_program;
        tick; @(negedge clk); rst=0;
        while (!busy) tick;
        // Both the core and memory model share reset, so the old response is cancelled.
        reset_core;
        await_halt("reset during accepted fetch then restart",HALT_EBREAK,expected_commits*4,0);
        $display("ALL %0d INTEGER CPU PROGRAM SCENARIOS PASSED",scenarios);
        $finish;
    end
    initial begin #1000000; $fatal(1,"GLOBAL TIMEOUT tb_fault_v_cpu"); end
endmodule
```

### 預期值表：program_init.svh

此檔案由 testbench 的 `include` 引入，與 testbench 放在相同 `verify` 資料夾。預期運算值為固定常數，不是讀取 DUT 結果產生。

```systemverilog
        program_words[0]=32'h00500093; expected_rd[0]=5'd1; expected_value[0]=32'h00000005;
        program_words[1]=32'hffd00113; expected_rd[1]=5'd2; expected_value[1]=32'hfffffffd;
        program_words[2]=32'h02000193; expected_rd[2]=5'd3; expected_value[2]=32'h00000020;
        program_words[3]=32'h01f00213; expected_rd[3]=5'd4; expected_value[3]=32'h0000001f;
        program_words[4]=32'h00100293; expected_rd[4]=5'd5; expected_value[4]=32'h00000001;
        program_words[5]=32'h00208333; expected_rd[5]=5'd6; expected_value[5]=32'h00000002;
        program_words[6]=32'h401103b3; expected_rd[6]=5'd7; expected_value[6]=32'hfffffff8;
        program_words[7]=32'h0020f433; expected_rd[7]=5'd8; expected_value[7]=32'h00000005;
        program_words[8]=32'h0020e4b3; expected_rd[8]=5'd9; expected_value[8]=32'hfffffffd;
        program_words[9]=32'h0020c533; expected_rd[9]=5'd10; expected_value[9]=32'hfffffff8;
        program_words[10]=32'h001125b3; expected_rd[10]=5'd11; expected_value[10]=32'h00000001;
        program_words[11]=32'h00113633; expected_rd[11]=5'd12; expected_value[11]=32'h00000000;
        program_words[12]=32'h004296b3; expected_rd[12]=5'd13; expected_value[12]=32'h80000000;
        program_words[13]=32'h0056d733; expected_rd[13]=5'd14; expected_value[13]=32'h40000000;
        program_words[14]=32'h4056d7b3; expected_rd[14]=5'd15; expected_value[14]=32'hc0000000;
        program_words[15]=32'h00329833; expected_rd[15]=5'd16; expected_value[15]=32'h00000001;
        program_words[16]=32'hffc08893; expected_rd[16]=5'd17; expected_value[16]=32'h00000001;
        program_words[17]=32'h00f17913; expected_rd[17]=5'd18; expected_value[17]=32'h0000000d;
        program_words[18]=32'h0100e993; expected_rd[18]=5'd19; expected_value[18]=32'h00000015;
        program_words[19]=32'hfff0ca13; expected_rd[19]=5'd20; expected_value[19]=32'hfffffffa;
        program_words[20]=32'hfff12a93; expected_rd[20]=5'd21; expected_value[20]=32'h00000001;
        program_words[21]=32'hfff0bb13; expected_rd[21]=5'd22; expected_value[21]=32'h00000001;
        program_words[22]=32'h01f29b93; expected_rd[22]=5'd23; expected_value[22]=32'h80000000;
        program_words[23]=32'h01fbdc13; expected_rd[23]=5'd24; expected_value[23]=32'h00000001;
        program_words[24]=32'h41fbdc93; expected_rd[24]=5'd25; expected_value[24]=32'hffffffff;
        program_words[25]=32'h12345d37; expected_rd[25]=5'd26; expected_value[25]=32'h12345000;
        program_words[26]=32'h00001d97; expected_rd[26]=5'd27; expected_value[26]=32'h00001068;
        program_words[27]=32'h678d0d13; expected_rd[27]=5'd26; expected_value[27]=32'h12345678;
        program_words[28]=32'h01130e33; expected_rd[28]=5'd28; expected_value[28]=32'h00000003;
        program_words[29]=32'h06300013; expected_rd[29]=5'd0; expected_value[29]=32'h00000000;
        program_words[30]=32'h01c00eb3; expected_rd[30]=5'd29; expected_value[30]=32'h00000003;
        program_words[31]=32'h00310f13; expected_rd[31]=5'd30; expected_value[31]=32'h00000000;
        program_words[32]=32'h80000fb7; expected_rd[32]=5'd31; expected_value[32]=32'h80000000;
        program_words[33]=32'hffff8f93; expected_rd[33]=5'd31; expected_value[33]=32'h7fffffff;
        program_words[34]=32'h001f8f93; expected_rd[34]=5'd31; expected_value[34]=32'h80000000;
        program_words[35]=32'h0ff0000f; expected_rd[35]=5'd0; expected_value[35]=32'h00000000;
        program_words[36]=32'h00000013; expected_rd[36]=5'd0; expected_value[36]=32'h00000000;
        program_words[37]=32'h00100073; program_len=38; expected_commits=37;
```

## ⑧ Vivado 模擬方式

1. 解壓縮檔案包，資料夾放在一般本機路徑。
2. Design Sources 加入 `rtl` 內的八個 `.sv`；`fault_v_pkg.sv` 編譯順序應在使用它的模組之前。
3. Simulation Sources 加入 `verify/tb_fault_v_cpu.sv` 及 `verify/program_init.svh`。如果 include 找不到，將 `verify` 的完整路徑加入 Simulation 的 Include Directories。
4. 把 **Simulation Top** 設成 `tb_fault_v_cpu`；若之後綜合，Design Top 才是 `fault_v_cpu`。
5. 執行 Behavioral Simulation，Tcl Console 輸入 `run all`。只跑 1000 ns 不足以跑完全部案例。
6. 檢查下方最後一行與 `$finish`；不能只看前幾筆 PASS。

`alu_program.mem` 和 `.S` 是同一段程式的參考檔；目前 testbench 透過 `program_init.svh` 載入，不需要把 `.mem` 當成 RTL 或手動新增 `$readmemh`。

預期關鍵輸出：

```text
PASS 1: dependent integer program committed=37 requests=38 pc=00000094 cause=9
PASS 2: dependent integer program committed=37 requests=38 pc=00000094 cause=9
PASS 3: dependent integer program committed=37 requests=38 pc=00000094 cause=9
PASS 4: load not yet supported committed=1 requests=2 pc=00000004 cause=1
PASS 5: branch not yet supported committed=1 requests=2 pc=00000004 cause=1
PASS 6: jump not yet supported committed=1 requests=2 pc=00000004 cause=1
PASS 7: MUL not supported committed=1 requests=2 pc=00000004 cause=1
PASS 8: illegal shift encoding committed=1 requests=2 pc=00000004 cause=1
PASS 9: ECALL stops with own cause committed=1 requests=2 pc=00000004 cause=8
PASS 10: fetch failure preserves prior write committed=1 requests=2 pc=00000004 cause=3
PASS 11: reset during accepted fetch then restart committed=37 requests=38 pc=00000094 cause=9
ALL 11 INTEGER CPU PROGRAM SCENARIOS PASSED
```

也可用 PowerShell 執行檔案包內 `run_xsim.ps1`。功能模擬不需要上板，不需要 FPGA pin constraints；模擬的 10 ns clock 只定義測試步進，並不代表 FPGA／ASIC 已達成 100 MHz 時序。

## ⑨ 檔案用途與後續整合界線

| 路徑 | 用途 |
| --- | --- |
| rtl/fault_v_cpu.sv | 真正 CPU top 及內部資料路徑 |
| rtl 其餘七個 .sv | 共用型別與既有功能模組 |
| verify/tb_fault_v_cpu.sv | 記憶體模擬、測試情境、commit 檢查 |
| verify/program_init.svh | 機器碼與固定預期值 |
| verify/alu_program.S／.mem | 組合語言與對應機器碼 |
| run_xsim.ps1 | 批次編譯與模擬 |
| logs/integer_cpu_results.log | 獨立模擬結果證據 |

接入 Branch／Jump 時需加入比較器、BranchTaken、目標對齊檢查及 link 寫回來源；接入 Load／Store 時需加入 MDR、byte enable、Store 對齊及 Load 擷取／擴展邏輯。**不能只移除 core_illegal 的限制就宣稱支援這些指令。**

綜合、FPGA 時序／實板驗證與 ASIC 實作是另外的驗收工作，應保留各自的報告。
