# Fault-V：CPU 系統整合與組合語言程式執行

## ① 系統用途與架構

`fault_v_cpu` 是 CPU 核心；`fault_v_soc` 在核心外接上指令記憶體、資料記憶體與完成狀態暫存器，形成可自行取指、執行與回報結果的系統。Testbench 提供 clock、reset 與結果檢查，不替 CPU 模擬記憶體交易。

| 項目 | 規格 |
| --- | --- |
| CPU | 延續 32-bit、多週期、依序執行的既有整合核心 |
| 指令記憶體 | 16 KiB，4096×32-bit，核心介面只讀 |
| 資料記憶體 | 16 KiB，4096×32-bit，支援 byte enable |
| 指令／資料介面 | 分離的請求／回應通道，全核心最多一筆未完成交易 |
| 完成狀態 | word MMIO，0x20000000，支援讀取及整個 word 寫入 |
| 程式啟動 | Reset PC＝0；指令影像預先初始化 |
| Reset | 高有效同步 reset；清 CPU、交易、狀態暫存器；保留 RAM 內容 |
| 時脈 | 核心、記憶體與狀態暫存器使用同一個 clock |
| 周邊 | 本系統只加入狀態暫存器；UART／GPIO 尚未加入 |
| 執行環境 | 裸機，專案自訂錯誤停止，沒有標準 trap／CSR／中斷 |

```text
                  fault_v_soc
┌───────────────────────────────────────────────────┐
│                    fault_v_cpu                    │
│       ALU、RegFile、Decoder、FSM、PC 等模組          │
│          │                         │              │
│          ▼                         ▼              │
│   指令請求／回應介面         資料請求／回應介面      │
│          │                         │              │
│          ▼                         ▼              │
│   u_imem：16 KiB             u_dmem：16 KiB         │
│   只讀指令影像                byte enable RAM       │
│                                    ＋             │
│                            MMIO 狀態暫存器         │
└───────────────────────────────────────────────────┘
       ▲ clk、rst        ▼ status、halt、debug、trace
```

分離實體記憶體是本系統的選擇，ISA 本身不強制如此。資料介面不能寫指令記憶體；本版沒有 self-modifying code 路徑。

## ② 位址配置與軟體使用方式

| 區域 | 位址範圍 | 用途 |
| --- | --- | --- |
| 指令記憶體 | 0x00000000～0x00003FFF | 程式從 0 開始；最後合法 word 位址 0x3FFC |
| 資料 RAM | 0x10000000～0x10003FFF | 變數、陣列與 stack；最後合法 word 位址 0x10003FFC |
| 狀態暫存器 | 0x20000000～0x20000003 | 32-bit 完成／失敗代碼；word 位址為 0x20000000 |
| 其他位址 | 未配置 | 回應存取失敗 |

核心仍要求指令／word 4-byte 對齊，halfword 2-byte 對齊；資料 endpoint 接收的是核心已對齊的 word 位址與 wstrb。MMIO 頁面 0x20000000～0x20000FFF 在核心只允許 word，系統目前只有 0x20000000 實際配置，其他 word 位址仍報錯。

| 程式狀態值 | 定義 |
| --- | --- |
| 0 | 尚未完成，或 reset 後初始狀態 |
| 1 | 程式回報成功 |
| 2 | 主程式總和檢查失敗 |
| 3 | Load 符號／零擴展檢查失敗 |
| 4 | 部分 Store／byte enable 檢查失敗 |
| 5 | 狀態暫存器讀回檢查失敗 |

硬體 fault 不會自動把狀態值改成軟體失敗代碼，要同時看 halted／halt_cause。這個範例的成功驗收是 **status＝1，且以 EBREAK 正常停止，並且資料結果正確**；不能只看到暫時的 status＝1 就忽略後續檢查。

## ③ 記憶體 endpoint 與交易契約

`fault_v_memory` 用同一個模組實例化指令記憶體與資料記憶體。讀寫在請求接受的上升緣執行，回應稍後有效並保持到接受。

| 參數 | 預設 | 用途 |
| --- | --- | --- |
| BASE_ADDR | 0x10000000 | RAM 映射基底；指令實例設定為 0 |
| WORDS | 4096 | 每個實例為 16 KiB |
| READ_ONLY | 0 | 指令實例為 1，拒絕寫入 |
| WITH_STATUS | 0 | 資料實例為 1，加入 MMIO 狀態 |
| INIT_FILE | 空字串 | 初始 hex 影像；空字串時初始內容全 0 |
| RESPONSE_DELAY | 1 | 接受請求後的等待 clock 數，最少 1 |

| 條件／事件 | 行為 |
| --- | --- |
| Idle，未 reset | req_ready＝1 |
| req_valid && req_ready，上升緣 | 接受一次請求，保存讀回 word／error；合法寫入當下生效 |
| 等待回應 | busy＝1，不接受第二筆請求 |
| 等待結束 | rsp_valid＝1；data／error 保持不變 |
| rsp_valid && rsp_ready，上升緣 | 消耗回應一次；之後才開放下一筆請求 |
| 無效或未對齊 word 位址 | error 回應，不修改 RAM |
| 寫 read-only RAM | error 回應，不修改 RAM |
| 寫狀態暫存器，但 wstrb≠1111 | error 回應，不修改狀態 |

Store 在 request acceptance 生效，成功回應是這筆交易已處理的確認；CPU 等待回應後才完成該指令。讀回資料在 acceptance 保存，即使 response 被阻擋也不變。

**這個系統與前一版 testbench 的記憶體模型有不同的明確契約：這裡寫入在接受時生效。** reset 清掉 pending／回應，不能撤銷已接受的 RAM 寫入；RAM 保留內容，狀態暫存器則清為 0。沒有跨 reset 的交易標籤，系統共同 reset 確保舊回應不送入重啟的 CPU。

記憶體的 `initial`／`$readmemh` 用於模擬與可支援初始化的 FPGA 流程，不是 ASIC SRAM／ROM 的製造初始化方案。本版沒有把 FPGA 記憶體推論等同於 ASIC memory macro。

## ④ 系統 Top 接腳與參數

| 參數 | 預設 | 用途 |
| --- | --- | --- |
| IMEM_FILE | 空字串 | 要放入指令記憶體的 `.mem` 檔 |
| IMEM_DELAY | 1 | 指令記憶體回應延遲 |
| DMEM_DELAY | 1 | 資料記憶體回應延遲 |

| 接腳 | 方向 | 用途 |
| --- | --- | --- |
| clk／rst | 輸入 | 單一 clock，高有效同步 reset |
| program_status[31:0] | 輸出 | 程式完成／失敗代碼 |
| halted／halt_cause | 輸出 | 核心停止及原因 |
| fault_pc／fault_addr／pc | 輸出 | 錯誤及 PC 觀察 |
| state | 輸出 | FSM 狀態 |
| retire_valid／retire_rd_we | 輸出 | 指令正常完成／是否真的寫入 rd |
| retire_pc／instruction／rd_data／rd_addr | 輸出 | 完成指令與寫回 trace |

trace 在 commit 的上升緣、非阻塞更新前取樣。它是專案自訂觀察介面，不是完整 RVFI。

## ⑤ 完整系統 RTL

整合包包含 **13 個 Design Sources**：既有 CPU 的 11 檔，加上下面的記憶體與系統 Top。既有 CPU 指令資料路徑沒有修改。

### 記憶體與狀態模組：fault_v_memory.sv

```systemverilog
`timescale 1ns/1ps
module fault_v_memory #(
    parameter logic [31:0] BASE_ADDR=32'h10000000,
    parameter integer WORDS=4096,
    parameter bit READ_ONLY=0,
    parameter bit WITH_STATUS=0,
    parameter string INIT_FILE="",
    parameter integer RESPONSE_DELAY=1
) (
    input logic clk,rst,
    input logic req_valid,
    output logic req_ready,
    input logic req_write,
    input logic [31:0] req_addr,req_wdata,
    input logic [3:0] req_wstrb,
    output logic rsp_valid,
    input logic rsp_ready,
    output logic [31:0] rsp_data,
    output logic rsp_err,
    output logic [31:0] program_status
);
    logic [31:0] mem[0:WORDS-1];
    logic busy;
    integer remaining;
    logic ram_hit,status_hit;
    logic [31:0] word_index;
    initial begin
        for (integer i=0;i<WORDS;i=i+1) mem[i]=0;
        if (INIT_FILE!="") $readmemh(INIT_FILE,mem);
    end
    assign word_index=(req_addr-BASE_ADDR)>>2;
    assign ram_hit=(req_addr>=BASE_ADDR) && (word_index<WORDS) && (req_addr[1:0]==0);
    assign status_hit=WITH_STATUS && (req_addr==32'h20000000);
    assign req_ready=!rst && !busy && !rsp_valid;
    always_ff @(posedge clk) begin
        if (rst) begin
            busy<=0; remaining<=0; rsp_valid<=0; rsp_data<=0; rsp_err<=0;
            program_status<=0;
            // RAM contents intentionally survive reset. Accepted writes are not undone.
        end else begin
            if (req_valid && req_ready) begin
                busy<=1; remaining<=(RESPONSE_DELAY<1)?1:RESPONSE_DELAY;
                rsp_data<=0; rsp_err<=0;
                if (ram_hit) begin
                    if (req_write && READ_ONLY) rsp_err<=1;
                    else begin
                        rsp_data<=mem[word_index];
                        if (req_write)
                            for (integer lane=0;lane<4;lane=lane+1)
                                if (req_wstrb[lane]) mem[word_index][lane*8 +: 8]<=req_wdata[lane*8 +: 8];
                    end
                end else if (status_hit) begin
                    if (req_write && (req_wstrb!=4'b1111)) rsp_err<=1;
                    else begin
                        rsp_data<=program_status;
                        if (req_write) program_status<=req_wdata;
                    end
                end else rsp_err<=1;
            end
            if (busy) begin
                if (remaining<=1) begin busy<=0; rsp_valid<=1; end
                else remaining<=remaining-1;
            end
            if (rsp_valid && rsp_ready) rsp_valid<=0;
        end
    end
endmodule
```

### 系統 Top：fault_v_soc.sv

```systemverilog
`timescale 1ns/1ps
module fault_v_soc #(
    parameter string IMEM_FILE="",
    parameter integer IMEM_DELAY=1,
    parameter integer DMEM_DELAY=1
) (
    input logic clk,rst,
    output logic [31:0] program_status,
    output logic halted,
    output fault_v_pkg::halt_cause_t halt_cause,
    output logic [31:0] fault_pc,fault_addr,pc,
    output fault_v_pkg::cpu_state_t state,
    output logic retire_valid,retire_rd_we,
    output logic [31:0] retire_pc,retire_instruction,retire_rd_data,
    output logic [4:0] retire_rd_addr
);
    logic imem_req_valid,imem_req_ready,imem_rsp_valid,imem_rsp_err,imem_rsp_ready;
    logic [31:0] imem_req_addr,imem_rsp_data;
    logic dmem_req_valid,dmem_req_ready,dmem_req_write,dmem_rsp_valid,dmem_rsp_err,dmem_rsp_ready;
    logic [31:0] dmem_req_addr,dmem_req_wdata,dmem_rsp_data;
    logic [3:0] dmem_req_wstrb;
    logic [31:0] unused_status;
    fault_v_cpu u_cpu(.*);
    fault_v_memory #(.BASE_ADDR(0),.READ_ONLY(1),.INIT_FILE(IMEM_FILE),.RESPONSE_DELAY(IMEM_DELAY)) u_imem(
        .clk(clk),.rst(rst),.req_valid(imem_req_valid),.req_ready(imem_req_ready),
        .req_write(1'b0),.req_addr(imem_req_addr),.req_wdata(32'b0),.req_wstrb(4'b0),
        .rsp_valid(imem_rsp_valid),.rsp_ready(imem_rsp_ready),.rsp_data(imem_rsp_data),
        .rsp_err(imem_rsp_err),.program_status(unused_status));
    fault_v_memory #(.BASE_ADDR(32'h10000000),.WITH_STATUS(1),.RESPONSE_DELAY(DMEM_DELAY)) u_dmem(
        .clk(clk),.rst(rst),.req_valid(dmem_req_valid),.req_ready(dmem_req_ready),
        .req_write(dmem_req_write),.req_addr(dmem_req_addr),.req_wdata(dmem_req_wdata),.req_wstrb(dmem_req_wstrb),
        .rsp_valid(dmem_rsp_valid),.rsp_ready(dmem_rsp_ready),.rsp_data(dmem_rsp_data),
        .rsp_err(dmem_rsp_err),.program_status(program_status));
endmodule
```

## ⑥ 主程式工作與 stack 使用

| 步驟 | 程式作用 | 預期結果 |
| --- | --- | --- |
| 啟動 | 設 x2＝stack top，x8＝資料 RAM 基底 | x2＝0x10004000，x8＝0x10000000 |
| Fibonacci 迴圈 | 把 F0～F9 存入十個 word | 0、1、1、2、3、5、8、13、21、34 |
| sum_fib | 從記憶體逐筆讀回累加 | 88 |
| double | 巢狀呼叫，總和加倍 | x10＝176 |
| 返回位址保存 | sum_fib 在 stack 保存 x1，再呼叫 double | 返回後恢復原 x1，x2 回到 stack top |
| 主程式檢查 | x10 與 176 比較 | 相同，將 176 存在 RAM＋0x40 |
| subword 檢查 | LB／LBU／LH／LHU，以及 SB／SH | 擴展與 byte lane 正確 |
| 完成 | FENCE、寫 status＝1、讀回檢查、EBREAK | status＝1，cause＝9，PC＝0xCC |

Stack top 指向 RAM 上界的下一個位址，只是初始 stack pointer；先減 4 再 SW，真正存取的是最後合法 word 0x10003FFC。這個範例示範返回位址保存，不代表完整 C ABI 驗證；通用 ABI 的 stack 對齊與所有 callee-saved 暫存器規則需要另行遵守。

### 完整 Assembly

```asm
.section .text
.globl _start
_start:
    lui x2,0x10004
    addi x2,x2,0
    lui x8,0x10000
    addi x8,x8,0
    addi x9,x8,0
    addi x10,x0,0
    addi x11,x0,1
    addi x12,x0,10
fib_loop:
    sw x10,0(x9)
    add x13,x10,x11
    addi x10,x11,0
    addi x11,x13,0
    addi x9,x9,4
    addi x12,x12,-1
    bne x12,x0,fib_loop
    jal x1,sum_fib
    addi x17,x0,176
    bne x10,x17,fail1
    sw x10,64(x8)
    lui x18,0x89abd
    addi x18,x18,-529
    sw x18,48(x8)
    lb x19,51(x8)
    addi x20,x0,-119
    bne x19,x20,fail2
    lbu x19,51(x8)
    addi x20,x0,137
    bne x19,x20,fail2
    lh x19,50(x8)
    lui x20,0xffff9
    addi x20,x20,-1621
    bne x19,x20,fail2
    lhu x19,50(x8)
    lui x20,0x9
    addi x20,x20,-1621
    bne x19,x20,fail2
    sb x0,49(x8)
    lui x21,0x1
    addi x21,x21,564
    sh x21,50(x8)
    lw x22,48(x8)
    lui x23,0x12340
    addi x23,x23,239
    bne x22,x23,fail3
    fence iorw,iorw
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,1
    sw x25,0(x24)
    lw x26,0(x24)
    bne x26,x25,fail4
    ebreak
sum_fib:
    addi x2,x2,-4
    sw x1,0(x2)
    addi x10,x0,0
    addi x14,x8,0
    addi x15,x0,10
sum_loop:
    lw x16,0(x14)
    add x10,x10,x16
    addi x14,x14,4
    addi x15,x15,-1
    bne x15,x0,sum_loop
    jal x1,double
    lw x1,0(x2)
    addi x2,x2,4
    jalr x0,0(x1)
double:
    add x10,x10,x10
    jalr x0,0(x1)
fail1:
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,2
    sw x25,0(x24)
    ebreak
fail2:
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,3
    sw x25,0(x24)
    ebreak
fail3:
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,4
    sw x25,0(x24)
    ebreak
fail4:
    lui x24,0x20000
    addi x24,x24,0
    addi x25,x0,5
    sw x25,0(x24)
    ebreak
```

本程式使用實際指令，沒有使用 `li`／`call` 等 pseudo-instruction。32-bit 常數由 LUI＋帶符號 ADDI 組成，例如 `0x89ABD000－529＝0x89ABCDEF`。

`.mem` 由專案的 Python 指令編碼器從相同的結構化指令清單產生，並由 RTL 執行驗證；這次沒有使用 GNU／LLVM assembler 編譯 `.S`，也沒有宣稱工具鏈／C 程式已整合。

### 主程式預期記憶體與結果

| 位址／訊號 | 預期結果 |
| --- | --- |
| 0x10000000～0x10000024 | 十個 word：0、1、1、2、3、5、8、13、21、34 |
| 0x10000030，subword 寫入後 | 0x123400EF |
| 0x10000040，計算結果 | 0x000000B0＝176 |
| 0x10003FFC，stack 保存返回位址 | 0x00000040 |
| x2 | 0x10004000，stack 已恢復 |
| x10 | 0x000000B0 |
| 正常完成指令數 | 175；迴圈反覆執行的指令逐次計入 |
| 資料交易數 | 33，包含 RAM、stack 及狀態暫存器 |
| 停止 | EBREAK，PC／fault_pc＝0xCC，fault_addr＝0 |

## ⑦ 系統驗收與錯誤程式

三個系統實例執行相同主程式，分別使用指令／資料延遲 1／1、2／3、3／5，並各 reset 後重跑一次。資料 RAM 保留內容，軟體重新寫入結果，驗證不是依賴每次 reset 自動清 RAM。

另有六個程式檢查硬體錯誤及軟體失敗回報：

| 程式 | 正常 commit | 資料交易 | status | cause | 停止 PC／fault_addr |
| --- | --- | --- | --- | --- | --- |
| illegal | 1 | 0 | 0 | 1 | `00000004`／`00000000` |
| misaligned | 2 | 0 | 0 | 4 | `00000008`／`10000001` |
| unmapped_store | 2 | 1 | 0 | 7 | `00000008`／`10004000` |
| fetch_error | 3 | 0 | 0 | 3 | `00004000`／`00004000` |
| unmapped_mmio | 2 | 1 | 0 | 6 | `00000008`／`20000004` |
| software_fail | 146 | 23 | 2 | 9 | `00000120`／`00000000` |

`software_fail` 故意把應比較的 176 改為 177，讓主程式進入 fail1，回報 status＝2 後 EBREAK。這代表測試本身正確識別了預期軟體失敗，不是把所有非零 status 都當成成功。

| 驗收項目 | 檢查方式 |
| --- | --- |
| 連續執行 | 每次 commit 比對 InstrPC、機器碼、rd enable／值及下一個 PC |
| 整個資料記憶體 | 停止時比較全部 4096 個 word，包含 stack 及未使用空間 |
| 架構暫存器 | 停止時比較全部 32 個 register |
| 交易 | 取指／資料請求與回應計數，全系統最多一筆 outstanding |
| 完成回報 | status、halt 原因、PC、fault context 同時符合預期 |
| Reset | CPU／status 清除，RAM 保留，軟體可重跑 |
| 記憶體 endpoint | response backpressure、byte enable、上界、只讀拒絕、status 寬度、reset 副作用 |

預期模型以 byte array 計算指令語意，不讀 DUT，也不照 FSM 的週期安排；測試程序只觀察內部記憶體，不替系統提供回應或寫入 CPU register。這是有限案例驗收，不是正式 ISA compliance 或所有輸入的完整證明。

## ⑧ 完整 Testbench

`program_expectations.svh` 包含七個程式的機器碼 trace 與最終狀態；`program_specs.json` 可查完整內容。下面的系統 testbench 必須與 `.svh` 和 `.mem` 一起使用。

### 系統程式驗證：tb_fault_v_soc.sv

```systemverilog
module tb_fault_v_soc;
    timeunit 1ns; timeprecision 1ps;
    import fault_v_pkg::*;
    logic clk=0;
    always #5 clk=~clk;
    // Batch script runs from sim/. For the Vivado GUI, set this to the absolute programs directory.
    localparam string IMAGE_DIR="../programs/";
    logic [8:0] done=0;
    for (genvar g=0;g<9;g=g+1) begin: cases
        localparam integer ID=(g<3)?0:g-2;
        localparam string FILE_NAME=(g<3)?"integration.mem":(g==3)?"illegal.mem":
            (g==4)?"misaligned.mem":(g==5)?"unmapped_store.mem":(g==6)?"fetch_error.mem":
            (g==7)?"unmapped_mmio.mem":"software_fail.mem";
        logic rst=1,halted,retire_valid,retire_rd_we;
        logic [31:0] program_status,fault_pc,fault_addr,pc,retire_pc,retire_instruction,retire_rd_data;
        logic [4:0] retire_rd_addr;
        halt_cause_t halt_cause,expected_cause;
        cpu_state_t state;
        logic [31:0] gold_pc[0:511],gold_inst[0:511],gold_data[0:511],gold_next[0:511];
        logic [4:0] gold_rd[0:511];
        logic [31:0] gold_regs[0:31],gold_ram[0:4095];
        logic [31:0] expected_fault_pc,expected_fault_addr,expected_status,previous_pc,previous_next;
        logic previous_commit;
        integer expected_count,expected_data_count,retired,fetches,data_requests,data_responses,cycles;
        logic [31:0] saved_tail;
        fault_v_soc #(.IMEM_FILE({IMAGE_DIR,FILE_NAME}),.IMEM_DELAY(g+1),.DMEM_DELAY(g*2+1)) dut(.*);
        task automatic must(input logic condition,input string label_text);
            if (condition!==1'b1) $fatal(1,"FAIL soc=%0d %s pc=%h retired=%0d",g,label_text,pc,retired);
        endtask
        task automatic load_expected(input integer id);
            for (integer k=0;k<4096;k=k+1) gold_ram[k]=0;
            `include "program_expectations.svh"
        endtask
        always @(posedge clk) begin
            if (rst) begin
                retired=0; fetches=0; data_requests=0; data_responses=0;
                previous_pc=0; previous_commit=0;
            end else begin
                if (previous_commit) must(pc===previous_next,"next PC");
                else must(pc===previous_pc,"PC held until commit");
                if (dut.imem_req_valid && dut.imem_req_ready) fetches=fetches+1;
                if (dut.dmem_req_valid && dut.dmem_req_ready) data_requests=data_requests+1;
                if (dut.dmem_rsp_valid && dut.dmem_rsp_ready) data_responses=data_responses+1;
                must(!((dut.u_imem.busy || dut.imem_rsp_valid) && (dut.u_dmem.busy || dut.dmem_rsp_valid)),"single outstanding system transaction");
                if (retire_valid) begin
                    must(retired<expected_count,"no extra commits");
                    must(retire_pc===gold_pc[retired] && retire_instruction===gold_inst[retired],"instruction trace");
                    must(retire_rd_we== (gold_rd[retired]!=0),"write enable");
                    must(retire_rd_addr===gold_rd[retired] && retire_rd_data===gold_data[retired],"writeback trace");
                    previous_next=gold_next[retired]; retired=retired+1;
                end
                previous_pc=pc; previous_commit=retire_valid;
            end
        end
        initial begin
            load_expected(ID);
            for (integer run_id=0;run_id<((g<3)?2:1);run_id=run_id+1) begin
                @(negedge clk); rst=1;
                repeat(3) begin @(posedge clk); #1; end
                must(pc==0 && program_status==0 && !halted,"reset PC status and halt");
                if (run_id>0) must(dut.u_dmem.mem[4095]===saved_tail,"RAM retained across reset");
                @(negedge clk); rst=0; cycles=0;
                while (!halted) begin
                    @(posedge clk); #1; cycles=cycles+1;
                    if (cycles>20000) $fatal(1,"TIMEOUT soc=%0d",g);
                end
                must(retired==expected_count && fetches==expected_count+1,"commit and fetch count");
                must(data_requests==expected_data_count && data_responses==expected_data_count,"request response counts");
                must(program_status===expected_status,"software completion status");
                must(halt_cause==expected_cause && fault_pc===expected_fault_pc && fault_addr===expected_fault_addr,"fault context");
                must(pc===expected_fault_pc,"stopped PC");
                for (integer r=0;r<32;r=r+1) must(dut.u_cpu.u_regfile.regs[r]===gold_regs[r],"all architecture registers");
                for (integer m=0;m<4096;m=m+1) must(dut.u_dmem.mem[m]===gold_ram[m],"all 16 KiB data RAM");
                saved_tail=dut.u_dmem.mem[4095];
                repeat(4) begin @(posedge clk); #1; end
                must(!retire_valid && !dut.imem_req_valid && !dut.dmem_req_valid,"halt remains inactive");
                $display("PASS soc=%0d run=%0d id=%0d commits=%0d data=%0d status=%h cause=%0d pc=%h",g,run_id,ID,retired,data_requests,program_status,halt_cause,pc);
            end
            done[g]=1;
        end
    end
    initial begin
        wait (&done); #1;
        $display("ALL 12 SOC PROGRAM RUNS PASSED"); $finish;
    end
    initial begin #2000000; $fatal(1,"GLOBAL TIMEOUT SOC"); end
endmodule
```

### 記憶體 endpoint 驗證：tb_fault_v_memory.sv

```systemverilog
module tb_fault_v_memory;
    timeunit 1ns; timeprecision 1ps;
    logic clk=0,rst=1,req_valid=0,req_ready,req_write=0,rsp_valid,rsp_ready=0,rsp_err;
    logic [31:0] req_addr=0,req_wdata=0,rsp_data,program_status;
    logic [3:0] req_wstrb=0;
    integer checks=0;
    logic ro_req_ready,ro_rsp_valid,ro_rsp_err;
    logic [31:0] ro_rsp_data,ro_status;
    always #5 clk=~clk;
    fault_v_memory #(.WORDS(4096),.WITH_STATUS(1),.RESPONSE_DELAY(3)) dut(.*);
    fault_v_memory #(.WORDS(4096),.READ_ONLY(1),.RESPONSE_DELAY(3)) rom(
        .clk(clk),.rst(rst),.req_valid(req_valid),.req_ready(ro_req_ready),.req_write(req_write),
        .req_addr(req_addr),.req_wdata(req_wdata),.req_wstrb(req_wstrb),
        .rsp_valid(ro_rsp_valid),.rsp_ready(rsp_ready),.rsp_data(ro_rsp_data),.rsp_err(ro_rsp_err),.program_status(ro_status));
    task automatic must(input logic condition,input string label_text);
        if (condition!==1'b1) $fatal(1,"FAIL memory %s",label_text);
    endtask
    task automatic transact(input logic wr,input logic [31:0] addr,data,input logic [3:0] mask,
                            input logic err,input logic [31:0] expected);
        @(negedge clk); req_valid=1; req_write=wr; req_addr=addr; req_wdata=data; req_wstrb=mask;
        @(posedge clk); must(req_ready,"accept request"); #1;
        @(negedge clk); req_valid=0;
        while (!rsp_valid) begin @(posedge clk); #1; end
        repeat(3) begin
            must(!req_ready && rsp_valid && rsp_err===err && rsp_data===expected,"held response under backpressure");
            must(!ro_req_ready && ro_rsp_valid && ro_rsp_data==0,"read-only RAM response held and contents unchanged");
            must(ro_rsp_err==(wr || addr<32'h10000000 || addr>=32'h10004000 || addr[1:0]!=0),"read-only RAM rejects writes and invalid addresses");
            @(posedge clk); #1;
        end
        @(negedge clk); rsp_ready=1;
        @(posedge clk); #1; must(!rsp_valid,"response consumed once");
        @(negedge clk); rsp_ready=0;
        checks=checks+1; $display("PASS memory %0d addr=%h wr=%0d error=%0d",checks,addr,wr,err);
    endtask
    initial begin
        repeat(2) begin @(posedge clk); #1; end
        @(negedge clk); rst=0;
        transact(1,32'h10000000,32'h89abcdef,4'hf,0,0);
        transact(0,32'h10000000,0,0,0,32'h89abcdef);
        transact(1,32'h10000000,32'h00005500,4'h2,0,32'h89abcdef);
        transact(0,32'h10000000,0,0,0,32'h89ab55ef);
        transact(1,32'h10003ffc,32'h12345678,4'hf,0,0);
        transact(0,32'h10003ffc,0,0,0,32'h12345678);
        transact(1,32'h10004000,32'hffffffff,4'hf,1,0);
        transact(0,32'h10000001,0,0,1,0);
        transact(1,32'h20000000,1,4'hf,0,0);
        transact(0,32'h20000000,0,0,0,1);
        transact(1,32'h20000000,99,4'h1,1,0);
        transact(0,32'h20000000,0,0,0,1);
        transact(0,32'h20000004,0,0,1,0);
        // Write is committed at acceptance; reset cancels only its outstanding response.
        @(negedge clk); req_valid=1; req_write=1; req_addr=32'h10000004; req_wdata=32'habcdef01; req_wstrb=4'hf;
        @(posedge clk); must(req_ready,"accepted write before reset"); #1;
        @(negedge clk); req_valid=0; rst=1;
        @(posedge clk); #1;
        must(!rsp_valid && program_status==0,"reset cancels response and clears status");
        @(negedge clk); rst=0;
        transact(0,32'h10000004,0,0,0,32'habcdef01);
        transact(0,32'h10003ffc,0,0,0,32'h12345678);
        transact(0,32'h20000000,0,0,0,0);
        $display("ALL 16 MEMORY ENDPOINT TRANSACTIONS PASSED"); $finish;
    end
    initial begin #20000; $fatal(1,"GLOBAL TIMEOUT MEMORY ENDPOINT"); end
endmodule
```

預期關鍵輸出：

```text
PASS soc=0 run=0 id=0 commits=175 data=33 status=00000001 cause=9 pc=000000cc
PASS soc=8 run=0 id=6 commits=146 data=23 status=00000002 cause=9 pc=00000120
ALL 12 SOC PROGRAM RUNS PASSED
```

另外單獨執行記憶體 testbench，最後應看到：

```text
ALL 16 MEMORY ENDPOINT TRANSACTIONS PASSED
```

多個系統同時模擬，各 PASS 的先後順序由延遲決定，不能用輸出順序推論 CPU 指令順序。16 筆 endpoint 測試同時檢查 RW 與只讀實例，另包含一筆接受後 reset 的寫入，用來檢查已接受的寫入保留。

## ⑨ 程式影像與 Vivado 操作

每個 `.mem` 包含 4096 行 32-bit hex word，第一行放在 PC＝0，後續每行位址加 4，程式之後補 0。剩餘 0 不是有效 NOP，程式必須自行停止或保持在合法路徑。

| 檔案／Top | 用途 |
| --- | --- |
| fault_v_cpu | CPU 核心，不含內建記憶體 |
| fault_v_soc | 整個系統 Design Top |
| tb_fault_v_soc | 主要 Simulation Top，執行程式與重跑驗證 |
| tb_fault_v_memory | 單獨的記憶體 Simulation Top |
| programs/integration.S／.mem | 主程式與指令影像 |
| programs 其他六組 .S／.mem | 預期錯誤與軟體失敗程式 |
| verify/program_expectations.svh | 必要的 include 預期表 |
| build_programs.py／program_model.py／assembler_support.py | 重產生機器碼與獨立預期值 |
| run_xsim.ps1 | 依序編譯與執行兩個 testbench，檢查最後 marker |

### 最容易重跑的方式

解壓縮後，在 PowerShell 切至檔案包資料夾，執行 `./run_xsim.ps1`。預設 Vivado 2022.2，可用 `-VivadoBin` 指定安裝位置。腳本在 `sim` 資料夾執行，testbench 的 `../programs/` 路徑可直接找到影像。

### Vivado GUI

1. Design Sources 加入 `rtl` 內 13 個 `.sv`，package 先編譯；避免同時加入舊版同名 RTL。
2. Simulation Sources 加入兩個 testbench 與 `program_expectations.svh`，必要時設定 `verify` Include Directory。
3. 在 `tb_fault_v_soc.sv` 把 **IMAGE_DIR** 改成解壓後 `programs` 的絕對路徑，使用 `/`，結尾保留 `/`，例如 `<HOME>/Downloads/Fault-V/programs/`。GUI 的工作目錄通常與批次腳本不同，不能直接假設相對路徑有效。
4. Simulation Top 選 **tb_fault_v_soc**，執行 Behavioral Simulation，再 `run all`。
5. 確認 `ALL 12 SOC PROGRAM RUNS PASSED`；再選 **tb_fault_v_memory** 重跑，確認 endpoint marker。

若之後以 `fault_v_soc` 作為綜合 Top，要設定 **IMEM_FILE** 為欲執行的程式影像，不能保留空字串卻期待它自動載入主程式。GUI testbench 的 IMAGE_DIR 只用在模擬，不會替綜合 Top 設定此參數。

此處沒有板卡 pin constraint、clock constraint 或板上程式載入介面。模擬 clock 的 10 ns 只是時間步進，不代表 FPGA 已達成 100 MHz。

## ⑩ 後續整合界線

這份系統已建立啟動、程式執行、記憶體讀寫、函式返回、錯誤停止與結果回報的完整功能路徑。接下來可在同一系統加入更全面的指令／程式驗證，以及 UART／GPIO、板卡 clock／reset、載入方式和 FPGA 約束。

RTL 功能模擬、FPGA 綜合／時序／實板、ASIC 記憶體實作與 sign-off 是各自的驗收工作。本文件不把模擬成功當成已可下片。
