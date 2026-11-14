# Fault-V：指令驗證與程式級驗收

## ① 驗證用途與系統範圍

本套件使用既有 `fault_v_soc`，包含 CPU、16 KiB 指令記憶體、16 KiB 資料 RAM 與 MMIO 狀態暫存器。工作重點是驗證，不新增或修改 CPU 功能。

| 層級 | 驗證重點 |
| --- | --- |
| 逐指令 | 每個支援名稱都有指定的 target instruction，檢查正常結果或該指令的停止行為 |
| 資料路徑 | signed／unsigned、立即數、位寬、移位、x0、同址讀寫 |
| 控制流程 | PC 更新、Branch 成立／不成立、跳躍、link、對齊 |
| 記憶體 | Load 擴展、Store mask、回應、原始錯誤位址、MMIO 限制 |
| 程式級 | 迴圈、資料相依、Fibonacci、函式／stack、記憶體複製 |
| 重跑 | RAM 保留內容，reset CPU 與 status 後重新執行 |

測試程式使用核心支援的 RV32I 指令名稱與本專案的 ECALL／EBREAK halt 行為。沒有加入標準 machine-mode trap／CSR／中斷，沒有做正式 ISA compliance 認證。

## ② 測試數量與延遲配置

| 類別 | 獨立案例 |
| --- | --- |
| 指定指令的 directed cases | 664 |
| 非法／未支援編碼 | 10 |
| 程式級案例 | 6 |
| 合計 | 680 |

每個案例在兩個真正的 RTL 系統上執行。六個程式在每個模式再重跑一次：`680×2＋6×2＝1372` 次系統執行。

| 模式 | 指令回應延遲 | 資料回應延遲 |
| --- | --- | --- |
| mode 0 | 1 clock | 1 clock |
| mode 1 | 4 clocks | 7 clocks |

延遲是 endpoint 的參數，不是 CPU 的時序驗收。10 ns 的模擬 clock 不代表 FPGA 已能達成 100 MHz。

## ③ 指令覆蓋表

下列數量是每個指令名稱的 focused case 數，不把 setup 指令或程式裡偶然執行的相同指令混入。每個 case 保存 target PC；驗收時確認這個位置真的完成，或依預期產生該指令的對齊／存取／停止事件。

| 指令 | focused cases | 覆蓋重點 |
| --- | --- | --- |
| ADD | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| SUB | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| SLL | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| SLT | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| SLTU | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| XOR | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| SRL | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| SRA | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| OR | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| AND | 21 | 0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2 |
| ADDI | 30 | imm＝-2048／-1／0／1／2047，多種運算元與目的暫存器 |
| SLTI | 30 | imm＝-2048／-1／0／1／2047，多種運算元與目的暫存器 |
| SLTIU | 30 | imm＝-2048／-1／0／1／2047，多種運算元與目的暫存器 |
| XORI | 30 | imm＝-2048／-1／0／1／2047，多種運算元與目的暫存器 |
| ORI | 30 | imm＝-2048／-1／0／1／2047，多種運算元與目的暫存器 |
| ANDI | 30 | imm＝-2048／-1／0／1／2047，多種運算元與目的暫存器 |
| SLLI | 24 | shamt＝0／1／15／31，正負與極值，x0／讀寫同址 |
| SRLI | 24 | shamt＝0／1／15／31，正負與極值，x0／讀寫同址 |
| SRAI | 24 | shamt＝0／1／15／31，正負與極值，x0／讀寫同址 |
| LUI | 10 | upper＝0／1／7FFFF／80000／FFFFF，非零 PC，rd＝x0 |
| AUIPC | 10 | upper＝0／1／7FFFF／80000／FFFFF，非零 PC，rd＝x0 |
| BEQ | 10 | 成立／不成立、相等、signed／unsigned 極值、未對齊目標 |
| BNE | 8 | 成立／不成立、相等、signed／unsigned 極值、未對齊目標 |
| BLT | 8 | 成立／不成立、相等、signed／unsigned 極值、未對齊目標 |
| BGE | 8 | 成立／不成立、相等、signed／unsigned 極值、未對齊目標 |
| BLTU | 8 | 成立／不成立、相等、signed／unsigned 極值、未對齊目標 |
| BGEU | 8 | 成立／不成立、相等、signed／unsigned 極值、未對齊目標 |
| JAL | 7 | 正／負位移、x0、link、對齊與位移邊界 |
| JALR | 10 | bit 0 清除、負立即數、立即數邊界、rd＝rs1、x0 |
| LB | 20 | 合法 lane、符號／零擴展、rd＝base／x0、對齊與存取錯誤 |
| LBU | 20 | 合法 lane、符號／零擴展、rd＝base／x0、對齊與存取錯誤 |
| LH | 13 | 合法 lane、符號／零擴展、rd＝base／x0、對齊與存取錯誤 |
| LHU | 13 | 合法 lane、符號／零擴展、rd＝base／x0、對齊與存取錯誤 |
| LW | 8 | 合法 lane、符號／零擴展、rd＝base／x0、對齊與存取錯誤 |
| SB | 19 | 合法 lane、部分寫入、x0、未對齊與存取錯誤 |
| SH | 12 | 合法 lane、部分寫入、x0、未對齊與存取錯誤 |
| SW | 7 | 合法 lane、部分寫入、x0、未對齊與存取錯誤 |
| FENCE | 1 | Store 已完成後繼續 Load，排序與 PC 正常完成 |
| ECALL | 1 | 先完成 Store，再以獨立原因停止；不產生正常 commit |
| EBREAK | 1 | 先完成 Store，再以獨立原因停止；不產生正常 commit |

ECALL／EBREAK 的覆蓋由正確的 halt 原因與 target PC 證明，不要求它們正常 retire。其他對齊／存取失敗案例也不應有正常 commit。

R-type 測試包含固定邊界及固定 seed＝20261007 的六組額外運算元；每次生成相同資料。這些是可重現的 operand 樣本，不是無限制 fuzzing。

### 覆蓋率的意思

`names＝40/40` 是 **本規格的指令名稱覆蓋**：每個名稱至少有 focused case 實際被驗收。它不是 RTL line／toggle／branch coverage，也不是所有位元組合、記憶體等待或 fault priority 的全組合證明。

## ④ 邊界值與錯誤規則

| 項目 | 測試重點 |
| --- | --- |
| 加減 | 結果保留低 32-bit，正負極值與溢位截斷 |
| signed 比較 | 0x80000000、0x7FFFFFFF、0xFFFFFFFF，避免減法符號誤判 |
| SLTIU | 立即數先符號擴展，再以 unsigned 比較；包含 -1 |
| R-type 移位 | 只取 rs2[4:0]，包含 0、31、32、63 及高位非零 |
| I-type 移位 | 合法 shamt 0／1／15／31；非法上位功能欄位另測 |
| x0／alias | 寫 x0 忽略；Load x0 仍發交易；rd＝來源時使用更新前資料 |
| Branch | 不成立時忽略未對齊目標；成立時檢查 4-byte 對齊 |
| JALR | 清 bit 0 後仍檢查 bit 1；rd＝rs1 保留舊 base |
| Load／Store | 全部合法 lane、部分 byte 保留、原始 fault_addr |
| byte／halfword 存取失敗 | 對外地址已對齊，但 fault_addr 保留 lane offset |
| MMIO | word-only；窄存取不發請求 |

另有 10 個非法案例：MUL、CSR、FENCE.I、非法 SLLI／JALR／Branch／Load／Store、非精確 ECALL 編碼及全 0 word。這些是非法編碼代表案例，不是枚舉全部 2^32 編碼。

## ⑤ 六個程式與預期結果

| case_id | 程式 | 預期結果 | 每次 commit | 每次資料交易 |
| --- | --- | --- | --- | --- |
| 674 | fibonacci_12 | F0～F11＝0、1、1、2、3、5、8、13、21、34、55、89 | 95 | 13 |
| 675 | loop_sum_100 | x3 與 RAM[0]＝5050 | 311 | 2 |
| 676 | gcd_48_18 | x10 與 RAM[0]＝6 | 27 | 2 |
| 677 | nested_call_aligned_stack | x10 與 RAM[0]＝42；sp 恢復 0x10004000 | 22 | 4 |
| 678 | memory_copy_64_checksum | 複製 64 words，checksum＝2016 | 719 | 193 |
| 679 | subword_signed_memory | 擴展正確；最後 word＝0x123400EF | 19 | 9 |

六個程式均以 FENCE、word status＝1 與 EBREAK 結束。Testbench 另外驗證輸出資料與 halt context，沒有只依賴程式自行回報成功。

### RAM 保留內容後重跑

每個程式先執行一次，再 reset CPU／status 後重跑；不清 RAM，不重新注入影像。第二次的預期模型由第一次的最終 RAM 開始，status 從 0 開始。

Store response 回傳的是寫入前舊 word，所以重跑的 response 可能與首次不同；模型保留第二次的預期 raw response，而最終結果與架構 trace 要一致。已接受的 RAM 寫入不因 reset 回滾。

### 完整 Assembly

#### fibonacci_12

```asm
.section .text
.globl _start
_start:
    lui x8,0x10000
    addi x8,x8,0
    addi x9,x8,0
    addi x10,x0,0
    addi x11,x0,1
    addi x12,x0,12
loop:
    sw x10,0(x9)
    add x13,x10,x11
    addi x10,x11,0
    addi x11,x13,0
    addi x9,x9,4
    addi x12,x12,-1
    bne x12,x0,loop
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
```

#### loop_sum_100

```asm
.section .text
.globl _start
_start:
    addi x1,x0,100
    addi x2,x0,0
    addi x3,x0,0
loop:
    addi x2,x2,1
    add x3,x3,x2
    blt x2,x1,loop
    lui x8,0x10000
    addi x8,x8,0
    sw x3,0(x8)
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
```

#### gcd_48_18

```asm
.section .text
.globl _start
_start:
    addi x10,x0,48
    addi x11,x0,18
loop:
    beq x10,x11,done
    bltu x10,x11,less
    sub x10,x10,x11
    jal x0,loop
less:
    sub x11,x11,x10
    jal x0,loop
done:
    lui x8,0x10000
    addi x8,x8,0
    sw x10,0(x8)
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
```

#### nested_call_aligned_stack

```asm
.section .text
.globl _start
_start:
    lui x2,0x10004
    addi x2,x2,0
    addi x10,x0,40
    jal x1,outer
    lui x8,0x10000
    addi x8,x8,0
    sw x10,0(x8)
    jal x0,done
outer:
    addi x2,x2,-16
    sw x1,12(x2)
    jal x1,inner
    addi x10,x10,1
    lw x1,12(x2)
    addi x2,x2,16
    jalr x0,0(x1)
inner:
    addi x10,x10,1
    jalr x0,0(x1)
done:
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
```

#### memory_copy_64_checksum

```asm
.section .text
.globl _start
_start:
    lui x8,0x10000
    addi x8,x8,0
    lui x9,0x10000
    addi x9,x9,512
    addi x10,x0,64
    addi x11,x0,0
fill:
    sw x11,0(x8)
    addi x8,x8,4
    addi x11,x11,1
    blt x11,x10,fill
    lui x8,0x10000
    addi x8,x8,0
    addi x11,x0,0
    addi x12,x0,0
copy:
    lw x13,0(x8)
    sw x13,0(x9)
    add x12,x12,x13
    addi x8,x8,4
    addi x9,x9,4
    addi x11,x11,1
    blt x11,x10,copy
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
```

#### subword_signed_memory

```asm
.section .text
.globl _start
_start:
    lui x8,0x10000
    addi x8,x8,0
    lui x1,0x89abd
    addi x1,x1,-529
    sw x1,0(x8)
    lb x2,3(x8)
    lbu x3,3(x8)
    lh x4,2(x8)
    lhu x5,2(x8)
    sb x0,1(x8)
    lui x6,0x1
    addi x6,x6,564
    sh x6,2(x8)
    lw x7,0(x8)
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    ebreak
```

巢狀函式範例分配 16-byte stack frame，先保存 ra，再呼叫內層，返回後恢復 ra／sp。這個測試使用對齊的 stack，但仍不代表完整 C ABI／toolchain 驗證。

`.S` 和 `.mem` 由專案的結構化指令清單產生；機器碼用 Python encoder 編碼，RTL 執行時與指令語意模型比較。這次沒有用 GNU／LLVM assembler，也沒有引入 C 程式。六份 `.mem` 各有 4096 words，可用於單獨初始化系統 Top。

## ⑥ Testbench 如何驗證

```text
build_suite.py
    ├→ ISA encoder → 每個案例的機器碼
    └→ 指令語意模型 → trace、交易、register、RAM、halt 預期值
                           │
                           ▼
                        suite.vec
                           │
                           ▼
                   tb_verification_suite
                           │
          reset 時裝入 ROM／準備 RAM fixture
                           │
                           ▼
                  真正 fault_v_soc 執行
                           │
                           ▼
           逐次比對交易／commit，停止時比對完整狀態
```

| 檢查點 | 比對內容 |
| --- | --- |
| 取指 | 每次正常／停止指令一筆取指，不重複執行 |
| 資料 request | 位址、方向、wdata、wstrb |
| 資料 response | raw word、error，每筆恰好一次回應 |
| Commit | InstrPC、指令 word、rd enable／編號／值、下一個 PC |
| 指令未完成 | PC 保持 |
| 交易數 | 全核心最多一筆 outstanding，與模型計數相符 |
| Halt | 原因、fault_pc、原始 fault_addr、PC、status |
| 最終狀態 | 32 個架構暫存器與全部 4096 個資料 RAM words |
| 覆蓋 | 指定 target PC 實際完成或以預期原因停止 |

預期模型以數學運算與 byte array 描述 ISA 行為，不讀 DUT、不模仿 FSM 的 cycle。零值 RAM 用 sparse table 表示，但 testbench 仍比較全部 words。

**每個新案例的初始 ROM／RAM 由 testbench 在 reset 下準備，屬於測試 fixture，不是硬體程式載入介面。**案例執行期間，記憶體 request／response 都由 RTL endpoint 處理；testbench 不修改 CPU register 或替核心完成指令。

## ⑦ 完整 Testbench

```systemverilog
module tb_verification_suite;
    timeunit 1ns; timeprecision 1ps;
    import fault_v_pkg::*;
    logic clk=0;
    always #5 clk=~clk;
    localparam string VECTOR_FILE="../verify/suite.vec";
    logic [1:0] done=0;
    for (genvar g=0;g<2;g=g+1) begin: modes
        logic rst=1,halted,retire_valid,retire_rd_we;
        logic [31:0] program_status,fault_pc,fault_addr,pc,retire_pc,retire_instruction,retire_rd_data;
        logic [4:0] retire_rd_addr;
        halt_cause_t halt_cause;
        cpu_state_t state;
        fault_v_soc #(.IMEM_DELAY((g==0)?1:4),.DMEM_DELAY((g==0)?1:7)) dut(.*);
        logic [31:0] gold_pc[0:4095],gold_inst[0:4095],gold_data[0:4095],gold_next[0:4095];
        logic [4:0] gold_rd[0:4095];
        logic [31:0] gold_regs[0:31],gold_ram[0:4095];
        logic [31:0] tx_addr[0:511],tx_data[0:511],tx_raw[0:511],tx_repeat_raw[0:511];
        logic [3:0] tx_mask[0:511];
        logic tx_write[0:511],tx_error[0:511];
        integer fd,total_cases,id,kind,focus_id,word_count,trace_count,tx_count,sparse_count,cause;
        logic [31:0] focus_pc,stop_pc,stop_addr,status_expected;
        integer retired,requests,responses,fetches,focus_hits,cycles,passed=0;
        integer scanned,temp_rd,temp_index,temp_write,temp_error;
        logic [31:0] temp_word,previous_pc,previous_next;
        logic previous_commit;
        logic [39:0] covered=0;
        task automatic must(input logic condition,input string label_text);
            if (condition!==1'b1) $fatal(1,"FAIL mode=%0d case=%0d %s pc=%h retired=%0d",g,id,label_text,pc,retired);
        endtask
        task automatic read_case;
            scanned=$fscanf(fd,"%d %d %d %h %d %d %d %d %d %h %h %h",id,kind,focus_id,focus_pc,word_count,trace_count,tx_count,sparse_count,cause,stop_pc,stop_addr,status_expected);
            must(scanned==12,"valid case header");
            must(word_count<=4096 && trace_count<=4096 && tx_count<=512,"vector bounds");
            for (integer m=0;m<4096;m=m+1) begin
                dut.u_imem.mem[m]=0; dut.u_dmem.mem[m]=0; gold_ram[m]=0;
            end
            for (integer m=0;m<word_count;m=m+1) begin
                scanned=$fscanf(fd,"%h",temp_word); must(scanned==1,"program word"); dut.u_imem.mem[m]=temp_word;
            end
            for (integer m=0;m<trace_count;m=m+1) begin
                scanned=$fscanf(fd,"%h %h %d %h %h",gold_pc[m],gold_inst[m],temp_rd,gold_data[m],gold_next[m]);
                must(scanned==5,"trace row");gold_rd[m]=temp_rd;
            end
            for (integer r=0;r<32;r=r+1) begin scanned=$fscanf(fd,"%h",gold_regs[r]); must(scanned==1,"register row"); end
            for (integer m=0;m<sparse_count;m=m+1) begin
                scanned=$fscanf(fd,"%d %h",temp_index,temp_word); must(scanned==2 && temp_index>=0 && temp_index<4096,"RAM row");
                gold_ram[temp_index]=temp_word;
            end
            for (integer m=0;m<tx_count;m=m+1) begin
                scanned=$fscanf(fd,"%h %d %h %h %h %d %h",tx_addr[m],temp_write,tx_data[m],tx_mask[m],tx_raw[m],temp_error,tx_repeat_raw[m]);
                must(scanned==7,"transaction row");tx_write[m]=temp_write;tx_error[m]=temp_error;
            end
        endtask
        always @(posedge clk) begin
            if (rst) begin
                retired=0;requests=0;responses=0;fetches=0;focus_hits=0;previous_pc=0;previous_commit=0;
            end else begin
                if (previous_commit) must(pc===previous_next,"next PC");
                else must(pc===previous_pc,"PC held until completion");
                if (dut.imem_req_valid && dut.imem_req_ready) fetches=fetches+1;
                if (dut.dmem_req_valid && dut.dmem_req_ready) begin
                    must(requests<tx_count,"no extra data request");
                    must(dut.dmem_req_addr===tx_addr[requests] && dut.dmem_req_write===tx_write[requests],"data address direction");
                    must(dut.dmem_req_wdata===tx_data[requests] && dut.dmem_req_wstrb===tx_mask[requests],"store payload and mask");
                    requests=requests+1;
                end
                if (dut.dmem_rsp_valid && dut.dmem_rsp_ready) begin
                    must(responses<tx_count,"no extra response");
                    must(dut.dmem_rsp_err===tx_error[responses] && dut.dmem_rsp_data===tx_raw[responses],"data response word and error");
                    responses=responses+1;
                end
                must(!((dut.u_imem.busy || dut.imem_rsp_valid) && (dut.u_dmem.busy || dut.dmem_rsp_valid)),"single outstanding transaction");
                if (retire_valid) begin
                    must(retired<trace_count,"no extra commit");
                    must(retire_pc===gold_pc[retired] && retire_instruction===gold_inst[retired],"instruction PC and word");
                    must(retire_rd_we==(gold_rd[retired]!=0),"rd enable including x0");
                    must(retire_rd_addr===gold_rd[retired] && retire_rd_data===gold_data[retired],"rd address and value");
                    if (focus_id>=0 && retire_pc==focus_pc) focus_hits=focus_hits+1;
                    previous_next=gold_next[retired];retired=retired+1;
                end
                previous_pc=pc;previous_commit=retire_valid;
            end
        end
        task automatic finish_check;
            must(retired==trace_count && fetches==trace_count+1,"commit and fetch count");
            must(requests==tx_count && responses==tx_count,"data count");
            must(halt_cause==cause && fault_pc===stop_pc && fault_addr===stop_addr && pc===stop_pc,"halt context");
            must(program_status===status_expected,"status including expected failure");
            for (integer r=0;r<32;r=r+1) must(dut.u_cpu.u_regfile.regs[r]===gold_regs[r],"all registers");
            for (integer m=0;m<4096;m=m+1) must(dut.u_dmem.mem[m]===gold_ram[m],"all data RAM words");
            if (focus_id>=0) begin
                must(focus_hits>0 || (fault_pc==focus_pc && cause!=1 && cause!=3),"target instruction actually exercised");
                covered[focus_id]=1;
            end
            repeat(3) begin @(posedge clk); #1; end
            must(!retire_valid && !dut.imem_req_valid && !dut.dmem_req_valid,"halt remains inactive");
            passed=passed+1;
        endtask
        initial begin
            fd=$fopen(VECTOR_FILE,"r"); must(fd!=0,"open suite vectors");
            scanned=$fscanf(fd,"%d",total_cases);must(scanned==1,"case count");
            for (integer c=0;c<total_cases;c=c+1) begin
                @(negedge clk);rst=1;
                @(posedge clk);#1;
                read_case;
                for (integer repeat_id=0;repeat_id<((kind==1)?2:1);repeat_id=repeat_id+1) begin
                    if (repeat_id>0) begin
                        @(negedge clk);rst=1;@(posedge clk);#1;
                        for (integer t=0;t<tx_count;t=t+1) tx_raw[t]=tx_repeat_raw[t];
                    end
                    must(pc==0 && program_status==0 && !halted,"clean core and status reset");
                    @(negedge clk);rst=0;cycles=0;
                    while (!halted) begin
                        @(posedge clk);#1;cycles=cycles+1;
                        if (cycles>100000) $fatal(1,"TIMEOUT mode=%0d case=%0d",g,id);
                    end
                    finish_check;
                    if (kind==1 || (id%50)==0) $display("PASS mode=%0d case=%0d repeat=%0d commits=%0d data=%0d status=%h",g,id,repeat_id,retired,requests,program_status);
                end
            end
            must(covered==40'hffffffffff,"40 of 40 instruction names observed");
            $display("COVERAGE mode=%0d names=40/40 bitmap=%h runs=%0d",g,covered,passed);
            $fclose(fd);done[g]=1;
        end
    end
    initial begin wait (&done);#1;$display("ALL 1372 ISA AND PROGRAM RUNS PASSED");$finish;end
    initial begin #20000000; $fatal(1,"GLOBAL TIMEOUT VERIFICATION SUITE");end
endmodule
```

### suite.vec 格式

| 順序 | 資料 |
| --- | --- |
| 檔案第一行 | case 總數 |
| 每個 case header | id、程式旗標、focus id／PC、word／trace／transaction／非零 RAM 數、cause、停止 PC／addr、status |
| program words | 每行一個 32-bit hex word |
| trace | PC、機器碼、rd、value、next PC |
| registers | x0～x31 的 32 行預期值 |
| sparse RAM | word index、value；未列出的預期值為 0 |
| transaction | addr、write、wdata、mask、raw、error、重跑的 raw |

不需手動編輯向量；`python build_suite.py` 可重產生。`suite.json` 保留可閱讀的案例名稱、指令、trace、交易與最後狀態；`coverage.json` 對應每個指令名稱的 case_id。

## ⑧ Vivado 操作與預期輸出

最直接的重現方式：解壓縮後，在檔案包資料夾用 PowerShell 執行 `./run_xsim.ps1`。預設 Vivado 2022.2，可傳入 `-VivadoBin` 調整。

GUI 操作：

1. Design Sources 加入 `rtl` 的 13 個 `.sv`，package 先編譯；只保留一套同名模組。
2. Simulation Sources 加入 `verify/tb_verification_suite.sv`。
3. 將 testbench 的 **VECTOR_FILE** 改成 `suite.vec` 的絕對路徑，使用 `/`。批次腳本的相對路徑是 `../verify/suite.vec`，GUI 工作目錄不一定相同。
4. Simulation Top 選 **tb_verification_suite**，執行 Behavioral Simulation，再 `run all`。
5. 確認兩個 COVERAGE 行與最後 PASS marker，沒有 Fatal。

```text
COVERAGE mode=0 names=40/40 bitmap=ffffffffff runs=686
COVERAGE mode=1 names=40/40 bitmap=ffffffffff runs=686
ALL 1372 ISA AND PROGRAM RUNS PASSED
```

日誌只顯示部分短案例 PASS 與所有程式 PASS；其餘短案例仍逐筆檢查，任何不符合預期的情況會立即 Fatal。兩個延遲模式同時模擬，輸出順序不一定固定。

| 檔案 | 用途 |
| --- | --- |
| rtl | 沿用的完整系統，13 個 RTL 檔案 |
| verify/tb_verification_suite.sv／suite.vec | 驗證環境與向量 |
| programs | 六份 Assembly 與完整記憶體影像 |
| isa_model.py／assembler_support.py | 指令語意與編碼 helper |
| build_suite.py | directed cases、程式與獨立預期值生成 |
| suite.json／coverage.json | 可閱讀案例與指令覆蓋對照 |
| run_xsim.ps1 | 編譯、模擬、PASS 與覆蓋 marker 檢查 |
| logs/verification_results.log | 原始驗證證據 |

## ⑨ 驗收界線

本套件驗收規格中的 40 個指令名稱、代表邊界與錯誤，以及六個程式的功能和 reset 重跑。CPU／系統 RTL 沿用已有版本，沒有因測試數增加而新增硬體功能。

尚未宣稱正式 RISC-V compliance、RTL code coverage、formal proof、完整 C ABI、FPGA 時序／實板或 ASIC sign-off。這些項目需要各自的驗證方式與報告，不能由本套件的 40/40 指令名稱覆蓋替代。
