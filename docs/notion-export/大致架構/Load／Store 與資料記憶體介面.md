# Load／Store 與資料記憶體介面

## ① 模組用途與整合範圍

這份 `fault_v_cpu` 在既有整數運算、Branch、JAL／JALR 上加入八種 Load／Store。CPU 能從資料記憶體讀取、運算，再把結果存回記憶體。

| 項目 | 規格 |
| --- | --- |
| 核心 | 32-bit，多周期，FSM 控制，一次一條指令 |
| Load | LB、LBU、LH、LHU、LW |
| Store | SB、SH、SW |
| 位址單位 | Byte addressing；位址加 1 表示前進 1 byte |
| 位元組順序 | Little-endian，低位 byte 放在低位址 |
| 外部資料介面 | 32-bit word 讀寫，4-bit byte enable，請求／回應握手 |
| 自然對齊 | Byte 任意；Halfword 2-byte；Word 4-byte |
| 未對齊處理 | 不拆成多筆交易，發出請求前停止並記錄原始位址 |
| 同時未完成交易 | 全核心最多一筆，包含指令及資料介面 |
| MMIO 規則 | 0x20000000～0x20000FFF 只允許 word 存取；其他位址由外部回應判定可存取性 |
| 完成回報 | 保留 word MMIO 狀態暫存器介面；周邊硬體尚未整合 |
| 例外環境 | 自訂 halt／debug，ECALL／EBREAK 分別停止，未加入標準 trap／CSR／中斷 |

整合版可執行規格中列出的 40 個 RV32I 指令名稱，包含前述整數、控制流程與 FENCE／ECALL／EBREAK 的專案行為。這不代表正式 ISA compliance 認證或完整 machine-mode；此處沒有快取、MMU 或作業系統。

| 指令 | 存取寬度 | 作用 |
| --- | --- | --- |
| LB | 8-bit | 讀取 byte，符號擴展為 32-bit |
| LBU | 8-bit | 讀取 byte，零擴展為 32-bit |
| LH | 16-bit | 讀取 halfword，符號擴展為 32-bit |
| LHU | 16-bit | 讀取 halfword，零擴展為 32-bit |
| LW | 32-bit | 讀取完整 word |
| SB | 8-bit | 寫出 rs2 的低 8-bit |
| SH | 16-bit | 寫出 rs2 的低 16-bit |
| SW | 32-bit | 寫出完整 rs2 |

有效位址都是 `A＋imm`，保留低 32-bit。Load 使用 I-type 符號擴展立即數，Store 使用 S-type；Store 的資料來自 B 保存的 rs2，不是立即數。

## ② 位址、byte lane 與 little-endian

```
ALUOut＝原始有效位址
    ├→ [31:2] 接上 00 → 外部 dmem_req_addr
    ├→ [1:0] → byte_offset → Load 擷取／Store 排列
    └→ 對齊檢查及 fault_addr（保留原始位址）
```

| 名稱 | 計算 | 例子：有效位址 0x10000003 |
| --- | --- | --- |
| 原始位址 | A＋imm | 0x10000003 |
| word 對齊位址 | {ALUOut[31:2],2'b00} | 0x10000000 |
| byte_offset | ALUOut[1:0] | 3 |
| byte lane | 位址對應的 word 內位置 | lane 3，資料 bits [31:24] |

Little-endian 下，word `0x89ABCDEF` 在連續四個位址的 byte 依序為 EF、CD、AB、89。對齊位址只是外部 word 介面的資料傳遞方式，CPU 原始位址仍是 byte address。

| lane | 位址 | 回應 word 中的 bits | SB 的 wstrb |
| --- | --- | --- | --- |
| 0 | aligned＋0 | [7:0] | 0001 |
| 1 | aligned＋1 | [15:8] | 0010 |
| 2 | aligned＋2 | [23:16] | 0100 |
| 3 | aligned＋3 | [31:24] | 1000 |

## ③ 整合 Datapath 與 MDR

```
IR → Decoder → mem_size、load_unsigned、wb_sel、instr_class
 │
 └→ imm_gen → I／S 立即數

Register File → A、B
                 │  │
A＋imm → ALU → ALUOut（原始地址）
                    ├→ FSM 對齊檢查 → 對外請求／等待
                    ├→ aligned address → dmem_req_addr
                    └→ byte_offset ───────────────┐
                                                │
B → store_align → dmem_req_wdata／wstrb           │
                                                │
dmem_rsp_data → MDR → load_extract ←─────────────┘
                          │
ALUOut／Load 結果／InstrPC＋4 → Writeback MUX → Register File rd

成功 Load：保存 MDR，下一狀態寫回並更新 PC
成功 Store：收到成功回應時完成並更新 PC，不寫 rd
```

| 保存位置／元件 | 用途 | 更新時機 |
| --- | --- | --- |
| A | 保存 rs1，計算 base＋offset | Decode 的 ab_we |
| B | 保存 rs2，供 Store 寫出 | Decode 的 ab_we |
| ALUOut | 保存原始有效位址 | ADDR_EXEC 的 aluout_we |
| MDR | 32-bit，保存完整原始回應 word | 成功 Load 回應握手的 mdr_we；reset 清 0 |
| load_extract | 根據 offset、size、unsigned 擷取／擴展 MDR | 組合邏輯 |
| store_align | 排列 B 的低 byte／halfword／word，產生 wstrb | 組合邏輯 |
| WB_LOAD | 選取 load_extract 結果 | LOAD_WB 寫回 |

讀取 x0 仍必須發出記憶體交易、處理錯誤，只忽略最後暫存器寫入。JALR 與 Load 的 rd＝rs1 都使用 Decode 保存的 A；寫回不會改變這條指令已保存的位址。

## ④ Load 擷取與擴展規則

先計算 `shifted＝MDR >> (byte_offset×8)`，再依寬度取低位資料。

| 模式 | 結果 |
| --- | --- |
| LB | {{24{shifted[7]}},shifted[7:0]} |
| LBU | {24'b0,shifted[7:0]} |
| LH | {{16{shifted[15]}},shifted[15:0]} |
| LHU | {16'b0,shifted[15:0]} |
| LW | MDR 原始 32-bit word |

本測試第一個 word 是 `0x5B12C980`：byte 依序為 80、C9、12、5B。

| 存取 | 預期結果 |
| --- | --- |
| LB lane 0／LBU lane 0 | FFFFFF80／00000080 |
| LB lane 1／LBU lane 1 | FFFFFFC9／000000C9 |
| LB lane 2／LBU lane 2 | 00000012／00000012 |
| LB lane 3／LBU lane 3 | 0000005B／0000005B |
| LH offset 0／LHU offset 0 | FFFFC980／0000C980 |
| LH offset 2／LHU offset 2 | 00005B12／00005B12 |
| LW offset 0 | 5B12C980 |

擷取模組不發出交易、不判斷存取失敗。FSM 在請求前保證自然對齊；不能把模組在非法 offset 下的組合值當成 CPU 支援未對齊存取。

## ⑤ Store 排列與 byte enable

每個 `wstrb[n]` 對應 `wdata[n*8 +: 8]`，只有啟用的 byte lane 可被記憶體更新。未啟用的 byte 必須保留原值。

以 B＝`0x89ABCDEF`、原 word＝`0x5B12C980` 為例：

| 指令／offset | 對外 wdata | wstrb | 寫入後 word |
| --- | --- | --- | --- |
| SB／0 | 000000EF | 0001 | 5B12C9EF |
| SB／1 | 0000EF00 | 0010 | 5B12EF80 |
| SB／2 | 00EF0000 | 0100 | 5BEFC980 |
| SB／3 | EF000000 | 1000 | EF12C980 |
| SH／0 | 0000CDEF | 0011 | 5B12CDEF |
| SH／2 | CDEF0000 | 1100 | CDEFC980 |
| SW／0 | 89ABCDEF | 1111 | 89ABCDEF |

store_align 對非法 halfword／word offset 輸出零遮罩；真正的錯誤停止仍由 FSM 決定。Load 的對外 wdata／wstrb 為 0，讀取寬度由核心在回應後擷取。

## ⑥ 記憶體握手與 FSM

| 訊號 | 方向 | 寬度 | 定義 |
| --- | --- | --- | --- |
| dmem_req_valid | 輸出 | 1 | 有資料請求；保持直到接受 |
| dmem_req_ready | 輸入 | 1 | 外部可接受請求 |
| dmem_req_write | 輸出 | 1 | 0＝讀，1＝寫 |
| dmem_req_addr | 輸出 | 32 | word 對齊的 byte address |
| dmem_req_wdata | 輸出 | 32 | 已排列的 Store 資料 |
| dmem_req_wstrb | 輸出 | 4 | 要更新的 byte lane |
| dmem_rsp_valid | 輸入 | 1 | 回應有效，包括 Store 的完成回應 |
| dmem_rsp_ready | 輸出 | 1 | 核心能接受回應 |
| dmem_rsp_data | 輸入 | 32 | 完整 word；Load 成功時保存 |
| dmem_rsp_err | 輸入 | 1 | 回應失敗 |

請求在 `req_valid && req_ready` 的上升緣接受；之後 CPU 不重複送出。回應在 `rsp_valid && rsp_ready` 的上升緣完成。請求首次接受的同一個 edge 不處理該交易的回應；外部須將回應資料、error 與 valid 保持到握手。

| 狀態 | 動作 | 正常下一步 |
| --- | --- | --- |
| DECODE | 保存 A／B，選擇 I／S immediate | ADDR_EXEC |
| ADDR_EXEC | A＋imm，保存 ALUOut | MEM_CHECK |
| MEM_CHECK | 檢查對齊、MMIO 寬度，不發交易 | LOAD_WAIT 或 STORE_WAIT |
| LOAD_WAIT，尚未接受 | 發出讀取請求；等待期間保持 payload | 接受後繼續等待回應 |
| LOAD_WAIT，成功回應 | mdr_we＝1，保存完整 word | LOAD_WB |
| LOAD_WB | reg_we、WB_LOAD、pc_we、instr_done | 寫回與 PC＋4，同時回 FETCH |
| STORE_WAIT，尚未接受 | 發出寫入請求；保持 wdata／wstrb | 接受後等待回應 |
| STORE_WAIT，成功回應 | pc_we、instr_done；不寫 rd | PC＋4，回 FETCH |
| 回應失敗 | 不寫回、不更新 PC，保存錯誤 | HALTED |

等待期間 IR、A、B、ALUOut、PC 保持；MDR 只在成功 Load 回應時更新。硬體沒有等待逾時機制，testbench 的 timeout 僅用來找模擬卡住。

FENCE 在本架構依序完成，前面的 Load／Store 都已收到回應，沒有待處理寫入緩衝。外部成功回應必須有相符的完成／排序語意；不能只回報「已排隊」卻假設其他主裝置已看到資料。

## ⑦ 錯誤、reset 與副作用界線

| 情況 | halt_cause | fault_addr | 是否發資料請求 |
| --- | --- | --- | --- |
| Load 未對齊 | HALT_LOAD_ALIGN＝4 | 原始有效位址 | 否 |
| Store 未對齊 | HALT_STORE_ALIGN＝5 | 原始有效位址 | 否 |
| MMIO 區窄 Load | HALT_LOAD_ACCESS＝6 | 原始有效位址 | 否 |
| MMIO 區窄 Store | HALT_STORE_ACCESS＝7 | 原始有效位址 | 否 |
| 外部 Load error | HALT_LOAD_ACCESS＝6 | 原始有效位址 | 是 |
| 外部 Store error | HALT_STORE_ACCESS＝7 | 原始有效位址 | 是 |
| 非法 memory 編碼 | HALT_ILLEGAL＝1 | 本專案為 0 | 否 |

fault_pc 指向發生錯誤的 Load／Store 指令，PC 保持該指令位址；對齊錯誤的判斷優先於 MMIO 寬度錯誤。失敗指令沒有正常 commit，也不寫目的暫存器。

- *CPU 不會回滾已發生的外部記憶體或 MMIO 副作用。**本測試 endpoint 規定成功 Store 在成功回應握手時生效，失敗 Store 不修改資料；這是測試環境的明確契約，不是 CPU 對任意外部 bus 的保證。

reset 測試讓核心與兩個記憶體模型一起取消 pending／舊回應，並重新初始化測試資料。真實系統要另定外部記憶體 reset／保留內容、交易取消與過期回應處理方式；不能只 reset 核心卻直接使用這個模型的假設。

## ⑧ 完整 RTL

使用這份整合包中的 **11 個 Design Sources**。同名 `fault_v_cpu.sv` 只保留最新一份，其他必要模組都要加入；Testbench 不加入硬體綜合。

### Load 擷取模組：load_extract.sv

```verilog
`timescale 1ns/1ps
module load_extract (
    input logic [31:0] word_data,
    input logic [1:0] byte_offset,
    input fault_v_pkg::mem_size_t mem_size,
    input logic load_unsigned,
    output logic [31:0] result
);
    import fault_v_pkg::*;
    logic [31:0] shifted;
    always_comb begin
        shifted=word_data >> {byte_offset,3'b000};
        result=32'b0;
        case (mem_size)
            MEM_BYTE: result=load_unsigned?{24'b0,shifted[7:0]}:{{24{shifted[7]}},shifted[7:0]};
            MEM_HALF: result=load_unsigned?{16'b0,shifted[15:0]}:{{16{shifted[15]}},shifted[15:0]};
            MEM_WORD: result=word_data;
            default: result=32'b0;
        endcase
    end
endmodule
```

### Store 排列模組：store_align.sv

```verilog
`timescale 1ns/1ps
module store_align (
    input logic [31:0] data,
    input logic [1:0] byte_offset,
    input fault_v_pkg::mem_size_t mem_size,
    output logic [31:0] wdata,
    output logic [3:0] wstrb
);
    import fault_v_pkg::*;
    always_comb begin
        wdata=32'b0; wstrb=4'b0;
        case (mem_size)
            MEM_BYTE: begin
                wdata={24'b0,data[7:0]} << {byte_offset,3'b000};
                wstrb=4'b0001 << byte_offset;
            end
            MEM_HALF: begin
                if (!byte_offset[0]) begin
                    wdata={16'b0,data[15:0]} << {byte_offset,3'b000};
                    wstrb=4'b0011 << byte_offset;
                end
            end
            MEM_WORD: begin
                if (byte_offset==0) begin wdata=data; wstrb=4'b1111; end
            end
            default: begin end
        endcase
    end
endmodule
```

### 完整 CPU Top：fault_v_cpu.sv

```verilog
`timescale 1ns/1ps
module fault_v_cpu (
    input logic clk, rst,
    output logic imem_req_valid,
    input logic imem_req_ready,
    output logic [31:0] imem_req_addr,
    input logic imem_rsp_valid, imem_rsp_err,
    input logic [31:0] imem_rsp_data,
    output logic imem_rsp_ready,
    // Data request/response interface: aligned word data with byte strobes.
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
    logic [31:0] ir,instr_pc,a_reg,b_reg,aluout,mdr;
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
    logic [31:0] wb_data,load_result,store_wdata;
    logic [3:0] store_wstrb;

    decoder u_decoder(.instruction(ir),.rs1_addr(rs1_addr),.rs2_addr(rs2_addr),.rd_addr(rd_addr),
        .instr_class(instr_class),.alu_op(alu_op),.imm_sel(imm_sel),
        .alu_src_a(alu_src_a),.alu_src_b(alu_src_b),.branch_op(branch_op),
        .mem_size(mem_size),.load_unsigned(load_unsigned),.rd_write(rd_write),
        .wb_sel(wb_sel),.illegal(decode_illegal));
    assign core_illegal=decode_illegal;

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
    load_extract u_load(.word_data(mdr),.byte_offset(aluout[1:0]),.mem_size(mem_size),
        .load_unsigned(load_unsigned),.result(load_result));
    store_align u_store(.data(b_reg),.byte_offset(aluout[1:0]),.mem_size(mem_size),
        .wdata(store_wdata),.wstrb(store_wstrb));
    always_comb begin
        case (wb_sel)
            WB_PC4: wb_data=instr_pc+32'd4;
            WB_LOAD: wb_data=load_result;
            default: wb_data=aluout;
        endcase
    end
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
        if (rst) begin ir<=0; instr_pc<=0; a_reg<=0; b_reg<=0; aluout<=0; branch_taken<=0; mdr<=0; end
        else begin
            if (ir_we) ir<=imem_rsp_data;
            if (instr_pc_we) instr_pc<=pc;
            if (ab_we) begin a_reg<=rs1_data; b_reg<=rs2_data; end
            if (aluout_we) begin
                if (instr_class==IC_JALR) aluout<={alu_result[31:1],1'b0};
                else aluout<=alu_result;
            end
            if (branch_taken_we) branch_taken<=branch_condition;
            if (mdr_we) mdr<=dmem_rsp_data;
        end
    end
    assign dmem_req_wdata=(instr_class==IC_STORE)?store_wdata:32'b0;
    assign dmem_req_wstrb=(instr_class==IC_STORE)?store_wstrb:4'b0;
    assign retire_valid=instr_done;
    assign retire_pc=instr_pc;
    assign retire_instruction=ir;
    assign retire_rd_we=instr_done && reg_we && (rd_addr!=0);
    assign retire_rd_addr=retire_rd_we?rd_addr:5'b0;
    assign retire_rd_data=retire_rd_we?wb_data:32'b0;
endmodule
```

## ⑨ 記憶體迴圈範例與預期結果

程式在 0x10000000、04、08、0C 分別存入 1、2、3、4，逐筆讀回並累加。最後的 FENCE 是正常指令，EBREAK 停止。

```nasm
.section .text
.globl _start
_start:
    lui x1,0x10000
    addi x1,x1,0
    addi x2,x1,0
    addi x3,x0,4
    addi x4,x0,1
    addi x5,x0,0
loop:
    sw x4,0(x2)
    lw x6,0(x2)
    add x5,x5,x6
    addi x2,x2,4
    addi x4,x4,1
    blt x4,x3,loop
    beq x4,x3,last
    ebreak
last:
    sw x4,0(x2)
    lw x6,0(x2)
    add x5,x5,x6
    fence iorw,iorw
    ebreak
```

| 項目 | 預期結果 |
| --- | --- |
| x5，累加結果 | 10＝0x0000000A |
| x6，最後讀回值 | 4 |
| x2，最後 Store／Load base | 0x1000000C |
| 四個 word | 00000001、00000002、00000003、00000004 |
| 資料交易 | 8 筆：4 次 Store＋4 次 Load |
| 正常 commit／取指 | 29／30 |
| 停止 | PC／fault_pc＝0x48、cause＝9、fault_addr＝0 |

模型中的資料記憶體是 256 bytes，位址為 0x10000000～0x100000FF；另外四個 bytes 在 0x20000000 用作 word MMIO 狀態 stub。這不是最終 16 KiB 記憶體，也不是已完成 UART／GPIO。

## ⑩ 驗證方法與完整 Testbench

| 驗證項目 | 驗收條件 |
| --- | --- |
| 五種 Load | 所有合法 lane、符號／零擴展與資料相依結果正確 |
| 三種 Store | wdata／wstrb 正確，未選中的 byte 保留 |
| 等待與握手 | request 穩定，只接受一次；每筆恰好一個完成回應 |
| 指令／資料介面 | 全核心最多一筆未完成交易 |
| 錯誤 | 未對齊不發請求；失敗不 commit、不寫 rd；原始 fault_addr 正確 |
| x0 | Load x0 仍讀取及處理錯誤；Store x0 寫入零 |
| 程式 | 負偏移、rd＝base、連續讀寫、迴圈與函式讀寫正確 |
| MMIO | 窄存取拒絕、word stub 讀寫及 FENCE 正確 |
| 回歸 | 原整數及控制流程程式的 trace 與最終狀態正確 |
| reset | 已接受 Load／Store 等待時共同 reset，從起點重跑正確 |

軟體預期模型以 byte array 表示記憶體，由指令運算元計算結果與 trace，不讀 DUT、也不照 FSM 的 cycle 安排運作。每個資料 request 都比對位址、方向、資料、遮罩；回應比對 raw word／error；每次 commit 比對指令、PC、寫回與下一個 PC；停止後比對全部 32 個暫存器與全部 260 個模型 bytes。

125 個程式各以兩種延遲執行，另有兩次等待資料回應時 reset 再重跑，共 252 組情境。這是有限的專案功能測試，不是正式 compliance suite 或所有輸入的證明。

`cases_init.svh` 是 testbench 必要的 include，包含完整機器碼與預期表；`cases.json` 保存每個程式的逐次 trace、交易與最終狀態。直接模擬現成檔案不需要先執行 Python。

```verilog
module tb_memory_cpu;
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

    logic [7:0] memory_bytes[0:259],golden_mem[0:259];
    logic [31:0] tx_addr[0:63],tx_data[0:63],tx_raw[0:63];
    logic tx_write[0:63],tx_error[0:63];
    logic [3:0] tx_mask[0:63];
    integer expected_transactions,transactions,responses,fail_write;
    logic [31:0] fail_addr;
    logic data_busy,data_stalled,captured_write;
    logic [31:0] captured_addr,captured_data,data_stalled_addr,data_stalled_value;
    logic [3:0] captured_mask,data_stalled_mask;
    logic data_stalled_write;
    integer data_request_timer,data_response_timer;
    function automatic logic mapped(input logic [31:0] addr);
        return (addr>=32'h10000000 && addr<32'h10000100) ||
               (addr>=32'h20000000 && addr<32'h20000004);
    endfunction
    function automatic integer mem_index(input logic [31:0] addr);
        if (addr>=32'h10000000 && addr<32'h10000100) return addr-32'h10000000;
        return 256+addr-32'h20000000;
    endfunction

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

    // Test endpoint: successful writes take effect only when the response handshakes.
    // Failed writes have no effect in this endpoint; this is not a universal bus guarantee.
    always @(posedge clk) begin
        if (rst) begin
            dmem_req_ready<=0; dmem_rsp_valid<=0; dmem_rsp_err<=0; dmem_rsp_data<=0;
            data_busy<=0; data_request_timer<=0; data_response_timer<=0;
            transactions<=0; responses<=0; captured_addr<=0; captured_write<=0;
            captured_data<=0; captured_mask<=0;
            for (integer m=0;m<260;m=m+1)
                memory_bytes[m]<=(m<256)?((m*73+128)&255):0;
        end else begin
            if (!data_busy) begin
                if (!dmem_rsp_valid) dmem_rsp_data<=32'hdeadbeef;
                if (dmem_req_valid && !dmem_req_ready) begin
                    if (data_request_timer>=((mode==0)?0:(transactions%4+1))) dmem_req_ready<=1;
                    else data_request_timer<=data_request_timer+1;
                end
                if (dmem_req_valid && dmem_req_ready) begin
                    must(transactions<expected_transactions,"no extra data transaction");
                    must(dmem_req_addr===tx_addr[transactions] && dmem_req_write===tx_write[transactions],"data address and direction");
                    must(dmem_req_wdata===tx_data[transactions] && dmem_req_wstrb===tx_mask[transactions],"store data and byte mask");
                    must(dmem_req_addr[1:0]==0,"external data address word aligned");
                    must(!busy && !imem_req_valid,"only one outstanding request across both channels");
                    transactions<=transactions+1; data_busy<=1; dmem_req_ready<=0;
                    captured_addr<=dmem_req_addr; captured_write<=dmem_req_write;
                    captured_data<=dmem_req_wdata; captured_mask<=dmem_req_wstrb;
                    data_response_timer<=(mode==0)?0:((transactions+mode)%6+1);
                end
            end else if (!dmem_rsp_valid) begin
                must(!dmem_req_valid,"accepted data transaction is not issued again");
                if (data_response_timer==0) begin
                    dmem_rsp_valid<=1;
                    if (!mapped(captured_addr) || (captured_addr==fail_addr && (fail_write<0 || captured_write==fail_write))) begin
                        dmem_rsp_err<=1; dmem_rsp_data<=0;
                    end else begin
                        dmem_rsp_err<=0;
                        dmem_rsp_data<={memory_bytes[mem_index(captured_addr)+3],memory_bytes[mem_index(captured_addr)+2],
                                        memory_bytes[mem_index(captured_addr)+1],memory_bytes[mem_index(captured_addr)]};
                    end
                end else data_response_timer<=data_response_timer-1;
            end
            if (dmem_rsp_valid && dmem_rsp_ready) begin
                must(dmem_rsp_err===tx_error[responses],"response error matches independent expected transaction");
                must(dmem_rsp_data===tx_raw[responses],"full raw response word matches byte-memory model");
                if (captured_write && !dmem_rsp_err)
                    for (integer lane=0;lane<4;lane=lane+1)
                        if (captured_mask[lane]) memory_bytes[mem_index(captured_addr)+lane]<=captured_data[lane*8 +: 8];
                responses<=responses+1; dmem_rsp_valid<=0; data_busy<=0; data_request_timer<=0;
            end
        end
    end

    // Commit trace is sampled before the same edge changes PC and RF.
    always @(posedge clk) begin
        if (rst) begin
            retired=0; stalled=0; previous_pc=0; previous_commit=0; data_stalled=0;
            for (integer r=0;r<32;r=r+1) expected_regs[r]=0;
        end else begin
            if (data_stalled) begin
                must(dmem_req_valid && dmem_req_addr===data_stalled_addr,"data request address stable under backpressure");
                must(dmem_req_write===data_stalled_write && dmem_req_wdata===data_stalled_value && dmem_req_wstrb===data_stalled_mask,"store payload stable under backpressure");
            end
            data_stalled=dmem_req_valid && !dmem_req_ready;
            data_stalled_addr=dmem_req_addr; data_stalled_write=dmem_req_write;
            data_stalled_value=dmem_req_wdata; data_stalled_mask=dmem_req_wstrb;
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
        must(transactions==expected_transactions && responses==expected_transactions,"all data requests receive exactly one response");
        for (integer m=0;m<260;m=m+1)
            must(memory_bytes[m]===golden_mem[m],"all memory bytes match independent model");
        repeat(4) tick;
        must(!imem_req_valid && !dmem_req_valid && !dmem_rsp_ready && !retire_valid && retired==expected_commits,"halt remains inactive");
        scenarios=scenarios+1;
        $display("PASS %0d: %s committed=%0d requests=%0d pc=%h cause=%0d data=%0d",scenarios,label_text,retired,requests,pc,halt_cause,transactions);
    endtask

    initial begin
        rst=1; mode=0; error_index=-1;
        for (case_id=0;case_id<125;case_id=case_id+1) begin
            for (delay_mode=0;delay_mode<2;delay_mode=delay_mode+1) begin
                @(negedge clk); rst=1; mode=delay_mode*2; load_case(case_id);
                tick; @(negedge clk); rst=0;
                await_halt(case_name,expected_cause,expected_fault_pc,expected_fault_addr);
            end
        end
        // Cancel an accepted store or load while the test endpoint has not responded.
        for (integer k=0;k<2;k=k+1) begin
            @(negedge clk); rst=1; mode=2; load_case(87);
            tick; @(negedge clk); rst=0;
            cycles=0;
            while (!(data_busy && captured_write==(k==0))) begin
                tick; cycles=cycles+1;
                if (cycles>3000) $fatal(1,"reset setup timeout");
            end
            reset_core;
            await_halt("reset during pending data transaction then restart",expected_cause,expected_fault_pc,expected_fault_addr);
        end
        $display("ALL %0d MEMORY CPU SCENARIOS PASSED",scenarios);
        $finish;
    end
    initial begin #2000000; $fatal(1,"GLOBAL TIMEOUT tb_memory_cpu"); end
endmodule
```

### 所有程式的預期結果

cause：1＝非法指令、2＝指令對齊、3＝取指失敗、4／5＝Load／Store 對齊、6／7＝Load／Store 存取失敗、8＝ECALL、9＝EBREAK。

| case_id | 程式 | commit | 資料交易 | 停止 PC | cause | fault_addr |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | integer instruction regression | 37 | 0 | `00000094` | 9 | `00000000` |
| 1 | beq a=ffffffff b=00000001 | 5 | 0 | `00000014` | 9 | `00000000` |
| 2 | beq a=00000001 b=ffffffff | 5 | 0 | `00000014` | 9 | `00000000` |
| 3 | beq a=00000007 b=00000007 | 4 | 0 | `00000014` | 9 | `00000000` |
| 4 | beq a=80000000 b=7fffffff | 7 | 0 | `0000001C` | 9 | `00000000` |
| 5 | beq taken target misaligned | 2 | 0 | `00000008` | 2 | `0000000A` |
| 6 | beq not taken target misaligned | 4 | 0 | `00000010` | 9 | `00000000` |
| 7 | bne a=ffffffff b=00000001 | 4 | 0 | `00000014` | 9 | `00000000` |
| 8 | bne a=00000001 b=ffffffff | 4 | 0 | `00000014` | 9 | `00000000` |
| 9 | bne a=00000007 b=00000007 | 5 | 0 | `00000014` | 9 | `00000000` |
| 10 | bne a=80000000 b=7fffffff | 6 | 0 | `0000001C` | 9 | `00000000` |
| 11 | bne taken target misaligned | 2 | 0 | `00000008` | 2 | `0000000A` |
| 12 | bne not taken target misaligned | 4 | 0 | `00000010` | 9 | `00000000` |
| 13 | blt a=ffffffff b=00000001 | 4 | 0 | `00000014` | 9 | `00000000` |
| 14 | blt a=00000001 b=ffffffff | 5 | 0 | `00000014` | 9 | `00000000` |
| 15 | blt a=00000007 b=00000007 | 5 | 0 | `00000014` | 9 | `00000000` |
| 16 | blt a=80000000 b=7fffffff | 6 | 0 | `0000001C` | 9 | `00000000` |
| 17 | blt taken target misaligned | 2 | 0 | `00000008` | 2 | `0000000A` |
| 18 | blt not taken target misaligned | 4 | 0 | `00000010` | 9 | `00000000` |
| 19 | bge a=ffffffff b=00000001 | 5 | 0 | `00000014` | 9 | `00000000` |
| 20 | bge a=00000001 b=ffffffff | 4 | 0 | `00000014` | 9 | `00000000` |
| 21 | bge a=00000007 b=00000007 | 4 | 0 | `00000014` | 9 | `00000000` |
| 22 | bge a=80000000 b=7fffffff | 7 | 0 | `0000001C` | 9 | `00000000` |
| 23 | bge taken target misaligned | 2 | 0 | `00000008` | 2 | `0000000A` |
| 24 | bge not taken target misaligned | 4 | 0 | `00000010` | 9 | `00000000` |
| 25 | bltu a=ffffffff b=00000001 | 5 | 0 | `00000014` | 9 | `00000000` |
| 26 | bltu a=00000001 b=ffffffff | 4 | 0 | `00000014` | 9 | `00000000` |
| 27 | bltu a=00000007 b=00000007 | 5 | 0 | `00000014` | 9 | `00000000` |
| 28 | bltu a=80000000 b=7fffffff | 7 | 0 | `0000001C` | 9 | `00000000` |
| 29 | bltu taken target misaligned | 2 | 0 | `00000008` | 2 | `0000000A` |
| 30 | bltu not taken target misaligned | 4 | 0 | `00000010` | 9 | `00000000` |
| 31 | bgeu a=ffffffff b=00000001 | 4 | 0 | `00000014` | 9 | `00000000` |
| 32 | bgeu a=00000001 b=ffffffff | 5 | 0 | `00000014` | 9 | `00000000` |
| 33 | bgeu a=00000007 b=00000007 | 4 | 0 | `00000014` | 9 | `00000000` |
| 34 | bgeu a=80000000 b=7fffffff | 6 | 0 | `0000001C` | 9 | `00000000` |
| 35 | bgeu taken target misaligned | 2 | 0 | `00000008` | 2 | `0000000A` |
| 36 | bgeu not taken target misaligned | 4 | 0 | `00000010` | 9 | `00000000` |
| 37 | backward loop and function return | 22 | 0 | `00000028` | 9 | `00000000` |
| 38 | nested calls preserving outer return register | 8 | 0 | `00000020` | 9 | `00000000` |
| 39 | JALR clears odd bit zero | 3 | 0 | `00000014` | 9 | `00000000` |
| 40 | JALR negative offset | 3 | 0 | `00000014` | 9 | `00000000` |
| 41 | JALR rd equals rs1 | 3 | 0 | `00000014` | 9 | `00000000` |
| 42 | JALR rd x0 | 3 | 0 | `00000014` | 9 | `00000000` |
| 43 | JALR offset bit zero | 3 | 0 | `00000014` | 9 | `00000000` |
| 44 | JALR clears bit0 but bit1 remains | 1 | 0 | `00000004` | 2 | `00000012` |
| 45 | JALR high aligned address fetch fails | 2 | 0 | `FFFFFFFC` | 3 | `FFFFFFFC` |
| 46 | JALR maximum positive immediate | 2 | 0 | `00000800` | 3 | `00000800` |
| 47 | JALR minimum negative immediate | 4 | 0 | `00000014` | 9 | `00000000` |
| 48 | JAL misaligned keeps link | 1 | 0 | `00000004` | 2 | `00000006` |
| 49 | JAL x0 skips instruction | 2 | 0 | `0000000C` | 9 | `00000000` |
| 50 | JAL high target fetch fails | 1 | 0 | `FFFFFFFC` | 3 | `FFFFFFFC` |
| 51 | JAL negative offset within program | 4 | 0 | `00000010` | 9 | `00000000` |
| 52 | branch displacement boundary 4092 | 1 | 0 | `00000FFC` | 3 | `00000FFC` |
| 53 | branch displacement boundary 4094 | 0 | 0 | `00000000` | 2 | `00000FFE` |
| 54 | branch displacement boundary -4096 | 1 | 0 | `FFFFF000` | 3 | `FFFFF000` |
| 55 | JAL displacement boundary 1048572 | 1 | 0 | `000FFFFC` | 3 | `000FFFFC` |
| 56 | JAL displacement boundary 1048574 | 0 | 0 | `00000000` | 2 | `000FFFFE` |
| 57 | JAL displacement boundary -1048576 | 1 | 0 | `FFF00000` | 3 | `FFF00000` |
| 58 | MUL illegal | 1 | 0 | `00000004` | 1 | `00000000` |
| 59 | reserved branch funct3 illegal | 1 | 0 | `00000004` | 1 | `00000000` |
| 60 | JALR nonzero funct3 illegal | 1 | 0 | `00000004` | 1 | `00000000` |
| 61 | jump target fetch error preserves link | 1 | 0 | `00000008` | 3 | `00000008` |
| 62 | ECALL regression | 1 | 0 | `00000004` | 8 | `00000000` |
| 63 | sequential fetch error regression | 1 | 0 | `00000004` | 3 | `00000004` |
| 64 | lb lane 0 | 4 | 1 | `00000010` | 9 | `00000000` |
| 65 | lb lane 1 | 4 | 1 | `00000010` | 9 | `00000000` |
| 66 | lb lane 2 | 4 | 1 | `00000010` | 9 | `00000000` |
| 67 | lb lane 3 | 4 | 1 | `00000010` | 9 | `00000000` |
| 68 | lbu lane 0 | 4 | 1 | `00000010` | 9 | `00000000` |
| 69 | lbu lane 1 | 4 | 1 | `00000010` | 9 | `00000000` |
| 70 | lbu lane 2 | 4 | 1 | `00000010` | 9 | `00000000` |
| 71 | lbu lane 3 | 4 | 1 | `00000010` | 9 | `00000000` |
| 72 | lh lane 0 | 4 | 1 | `00000010` | 9 | `00000000` |
| 73 | lh lane 2 | 4 | 1 | `00000010` | 9 | `00000000` |
| 74 | lhu lane 0 | 4 | 1 | `00000010` | 9 | `00000000` |
| 75 | lhu lane 2 | 4 | 1 | `00000010` | 9 | `00000000` |
| 76 | lw lane 0 | 4 | 1 | `00000010` | 9 | `00000000` |
| 77 | sb lane 0 preserves other bytes | 6 | 2 | `00000018` | 9 | `00000000` |
| 78 | sb lane 1 preserves other bytes | 6 | 2 | `00000018` | 9 | `00000000` |
| 79 | sb lane 2 preserves other bytes | 6 | 2 | `00000018` | 9 | `00000000` |
| 80 | sb lane 3 preserves other bytes | 6 | 2 | `00000018` | 9 | `00000000` |
| 81 | sh lane 0 preserves other bytes | 6 | 2 | `00000018` | 9 | `00000000` |
| 82 | sh lane 2 preserves other bytes | 6 | 2 | `00000018` | 9 | `00000000` |
| 83 | sw lane 0 preserves other bytes | 6 | 2 | `00000018` | 9 | `00000000` |
| 84 | mixed signed loads and negative offsets | 13 | 8 | `00000034` | 9 | `00000000` |
| 85 | dependent loads stores and rd equals base | 9 | 4 | `00000024` | 9 | `00000000` |
| 86 | load x0 still reads and store x0 writes zero | 5 | 3 | `00000014` | 9 | `00000000` |
| 87 | memory loop sum with FENCE | 29 | 8 | `00000048` | 9 | `00000000` |
| 88 | function with memory access | 8 | 2 | `00000020` | 9 | `00000000` |
| 89 | lh rejects offset 1 | 3 | 0 | `0000000C` | 4 | `10000001` |
| 90 | lh rejects offset 3 | 3 | 0 | `0000000C` | 4 | `10000003` |
| 91 | lhu rejects offset 1 | 3 | 0 | `0000000C` | 4 | `10000001` |
| 92 | lhu rejects offset 3 | 3 | 0 | `0000000C` | 4 | `10000003` |
| 93 | lw rejects offset 1 | 3 | 0 | `0000000C` | 4 | `10000001` |
| 94 | lw rejects offset 2 | 3 | 0 | `0000000C` | 4 | `10000002` |
| 95 | lw rejects offset 3 | 3 | 0 | `0000000C` | 4 | `10000003` |
| 96 | sh rejects offset 1 | 3 | 0 | `0000000C` | 5 | `10000001` |
| 97 | sh rejects offset 3 | 3 | 0 | `0000000C` | 5 | `10000003` |
| 98 | sw rejects offset 1 | 3 | 0 | `0000000C` | 5 | `10000001` |
| 99 | sw rejects offset 2 | 3 | 0 | `0000000C` | 5 | `10000002` |
| 100 | sw rejects offset 3 | 3 | 0 | `0000000C` | 5 | `10000003` |
| 101 | lb injected response error | 3 | 1 | `0000000C` | 6 | `10000000` |
| 102 | lbu injected response error | 3 | 1 | `0000000C` | 6 | `10000000` |
| 103 | lh injected response error | 3 | 1 | `0000000C` | 6 | `10000000` |
| 104 | lhu injected response error | 3 | 1 | `0000000C` | 6 | `10000000` |
| 105 | lw injected response error | 3 | 1 | `0000000C` | 6 | `10000000` |
| 106 | sb injected response error | 3 | 1 | `0000000C` | 7 | `10000000` |
| 107 | sh injected response error | 3 | 1 | `0000000C` | 7 | `10000000` |
| 108 | sw injected response error | 3 | 1 | `0000000C` | 7 | `10000000` |
| 109 | load x0 response error still halts | 2 | 1 | `00000008` | 6 | `10000000` |
| 110 | lb unmapped address | 2 | 1 | `00000008` | 6 | `10000100` |
| 111 | lw unmapped address | 2 | 1 | `00000008` | 6 | `10000100` |
| 112 | sb unmapped address | 2 | 1 | `00000008` | 7 | `10000100` |
| 113 | sw unmapped address | 2 | 1 | `00000008` | 7 | `10000100` |
| 114 | lb rejects narrow MMIO without request | 2 | 0 | `00000008` | 6 | `20000000` |
| 115 | lbu rejects narrow MMIO without request | 2 | 0 | `00000008` | 6 | `20000000` |
| 116 | lh rejects narrow MMIO without request | 2 | 0 | `00000008` | 6 | `20000000` |
| 117 | lhu rejects narrow MMIO without request | 2 | 0 | `00000008` | 6 | `20000000` |
| 118 | sb rejects narrow MMIO without request | 2 | 0 | `00000008` | 7 | `20000000` |
| 119 | sh rejects narrow MMIO without request | 2 | 0 | `00000008` | 7 | `20000000` |
| 120 | misalignment has priority over narrow MMIO | 2 | 0 | `00000008` | 4 | `20000001` |
| 121 | word MMIO status stub | 6 | 2 | `00000018` | 9 | `00000000` |
| 122 | illegal memory funct3 00003083 | 2 | 0 | `00000008` | 1 | `00000000` |
| 123 | illegal memory funct3 00006083 | 2 | 0 | `00000008` | 1 | `00000000` |
| 124 | illegal memory funct3 00003023 | 2 | 0 | `00000008` | 1 | `00000000` |

最後兩次 reset 情境重跑記憶體迴圈，預期關鍵輸出：

```
PASS 251: reset during pending data transaction then restart committed=29 requests=30 pc=00000048 cause=9 data=8
PASS 252: reset during pending data transaction then restart committed=29 requests=30 pc=00000048 cause=9 data=8
ALL 252 MEMORY CPU SCENARIOS PASSED
```

## ⑪ Vivado 使用與檔案配置

1. 解壓縮整合包至一般本機資料夾。
2. Design Sources 加入 `rtl` 內 11 個 `.sv`。`fault_v_pkg.sv` 先編譯，避免同時加入舊版本的同名檔案。
3. Simulation Sources 加入 `verify/tb_memory_cpu.sv` 與 `verify/cases_init.svh`。找不到 include 時，把 `verify` 的完整路徑加入 Simulation Include Directories。
4. Simulation Top 設為 **tb_memory_cpu**；Design Top 是 **fault_v_cpu**。
5. 執行 Behavioral Simulation，Tcl Console 輸入 **run all**；1000 ns 不足以跑完。
6. 確認最後的 `ALL 252 MEMORY CPU SCENARIOS PASSED`、正常 `$finish`，沒有 Fatal。

| 檔案 | 用途 |
| --- | --- |
| rtl/fault_v_cpu.sv | 整合運算、控制流程及資料讀寫的 CPU Top |
| rtl/load_extract.sv／store_align.sv | 讀回擷取／擴展、寫出資料／遮罩 |
| rtl 其他八檔 | ALU、imm_gen、RegFile、PC、Decoder、FSM、Branch Comparator、package |
| verify/tb_memory_cpu.sv／cases_init.svh | 模擬環境與完整預期表 |
| verify/memory_loop.S／memory_loop.mem | 可閱讀程式與對應機器碼 |
| cases.json | 全部程式、預期 trace、交易、暫存器與記憶體 |
| reference_model.py／build_cases.py／make_tb.py | 重產生預期資料與 testbench 的 Python 工具 |
| reference_inputs | 回歸資料與模板；不加入 Simulation Sources |
| run_xsim.ps1 | XSim 編譯、elaboration、模擬及 PASS 檢查 |
| logs/memory_cpu_results.log | 獨立模擬證據 |

也可在 PowerShell 執行 `run_xsim.ps1`；預設 Vivado 2022.2 路徑，可傳入 `-VivadoBin` 調整。若要重產生測試資料，依序執行 `python build_cases.py`、`python make_tb.py`。

這份 RTL 是後續整合的基礎，還要加入實際記憶體、載入程式方式、UART／GPIO、clock／reset 與 FPGA 約束。功能模擬的 10 ns clock 不代表硬體已達到 100 MHz；本文件沒有宣稱 FPGA 時序、實板或 ASIC sign-off 通過。