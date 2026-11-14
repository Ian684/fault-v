# Fault-V：UART 與 GPIO

## 1．模組用途與規格

CPU 透過 Load／Store 存取周邊暫存器，控制 UART 傳送與板上 LED、讀取板上開關。這些周邊與 CPU 共用 25 MHz 核心時脈，保持單一未完成資料交易。

| 項目 | 規格 |
| --- | --- |
| 系統 Top | `fault_v_soc` |
| FPGA Top | `fault_v_fpga_top` |
| 主要平台 | PYNQ-Z2，`xc7z020clg400-1` |
| 核心 clock | 25 MHz；由 125 MHz 經 MMCM 產生 |
| CPU | 延續多周期 RV32I 基礎核心與自訂停止介面 |
| 周邊存取 | Memory-mapped I/O；程式使用 `LW`／`SW` |
| UART | 僅 TX；8 data bits、無 parity、1 stop bit，LSB first |
| UART baud | 目標 115200；實際 25,000,000 ÷ 217 ≈ 115207.37 baud |
| TX 緩衝 | 一個正在傳送的 frame；沒有 FIFO |
| GPIO output | 4-bit，接四顆一般 LED |
| GPIO input | 2-bit，接 SW0／SW1，FPGA 外層以兩級 FF 同步 |
| Reset | UART 回 idle high、取消未完成 frame；GPIO output 清零 |
| CPU halt | 周邊持續有 clock；UART 可繼續傳送，GPIO 維持最後值 |
| 作業環境 | 裸機組合語言，不需要 ARM 執行本程式 |

核心 ALU、Decoder、Register File、PC、FSM 的指令語意不因周邊而改變。GPIO 的四個 bit 才是程式可控制的輸出；LED 不再固定顯示 heartbeat／halt 狀態。

## 2．位址配置與暫存器

| 位址 | 名稱 | 存取 | 位元與行為 |
| --- | --- | --- | --- |
| `0x00000000～0x00003FFF` | IMEM | 取指 | 16 KiB，FPGA 預先初始化 |
| `0x10000000～0x10003FFF` | DMEM | R／W | 16 KiB，保留原資料存取規則 |
| `0x20000000` | PROGRAM_STATUS | R／W | 0＝未完成、1＝成功、其他非零＝失敗碼 |
| `0x20000100` | UART_TX_DATA | W | 寫入低 8-bit，啟動一個 UART frame；高 24-bit 忽略 |
| `0x20000104` | UART_TX_STATUS | R | bit 0＝ready、bit 1＝busy，其餘為 0 |
| `0x20000200` | GPIO_OUT | R／W | 低 4-bit 為 LED0～3；高 28-bit 讀到 0，寫入忽略 |
| `0x20000204` | GPIO_IN | R | 低 2-bit 為 SW0／SW1；高 30-bit 為 0 |

| UART status | 數值 | 意義 |
| --- | --- | --- |
| ready＝1、busy＝0 | `0x00000001` | UART 可以接受下一個 byte |
| ready＝0、busy＝1 | `0x00000002` | 正在傳送 start／data／stop bits |

status 是讀取請求接受時的快照。即使 UART 之後從 busy 變 idle，該回應在等待 CPU 接受期間仍保持原值。

`UART_TX_DATA` 不可讀；UART status 與 GPIO input 不可寫。非法存取回報 error，由 CPU 保存 fault 資訊並停止。位址區域內其他 offset（例如 `0x20000108`）也會回報 error。

**本 MMIO page 只允許 word 存取。**即使 UART 資料只有 8-bit，也以 `SW` 寫入，使用 `4'b1111` write strobe。`SB`／`SH`／`LB`／`LH` 等窄幅存取由 CPU 拒絕；未對齊存取依既定優先順序先回報 alignment fault。資料 RAM 的 byte／halfword 存取仍然支援。

## 3．資料介面與路由

```text
                       Fault-V CPU
                            │
                 dmem request／response
                            │
                  SoC 資料路由與保存選擇
                    │                 │
               RAM／原狀態         UART／GPIO
                    │                 │
             fault_v_memory       fault_v_io
            DMEM + PROGRAM_STATUS    │       │
                                    ▼       ▼
                                  uart_tx  gpio_out
                                    │       │
                                Pmod B1   LED0～3
                                            ▲
SW0／SW1 → 兩級同步 → gpio_in → GPIO_IN ──────┘
```

| 路由訊號 | 功能 |
| --- | --- |
| `io_hit` | `0x20000100～0x2000010F` 或 `0x20000200～0x2000020F` 選到 IO 端點 |
| `bus_pending` | 已接受請求，尚未完成回應握手 |
| `selected_io` | 保存這笔交易的目的端點，避免回應期間隨 CPU 位址變化 |
| `ram_req_valid`／`io_req_valid` | 只向選到的端點送一筆請求 |
| `ram_rsp_ready`／`io_rsp_ready` | 只接受保存的端點回應 |

| 階段 | 規則 |
| --- | --- |
| 尚未接受請求 | `req_valid` 與地址、資料、strobe 保持；等待選定端點 ready |
| 請求接受 | 同一個 clock 上升緣 valid 與 ready 都為 1；保存端點 |
| 周邊副作用 | 接受 `SW UART_TX_DATA` 時啟動傳送；接受 `SW GPIO_OUT` 時更新 LED |
| 等待回應 | 不再送新交易；回應 valid、data、error 維持至握手 |
| 回應完成 | CPU 接受後才釋放 pending；下一筆交易於後續 cycle 開始 |
| Reset | 清除路由與回應狀態；不撤銷已被外部接收的 UART bits |

此路由保留 `u_dmem.mem` 與原來 RAM／status 行為，方便沿用既有測試。非法區域不默認成功。

## 4．UART 傳送架構

| 項目 | 規則 |
| --- | --- |
| 模組 | `uart_tx` |
| 輸入 | `clk`、`rst`、`start`、`data[7:0]` |
| 輸出 | `tx`、`busy` |
| Idle | `tx＝1`、`busy＝0` |
| Start | 接受 start 時擷取 data，`tx＝0` |
| Data | 依序送 data[0]～data[7] |
| Stop | `tx＝1`，仍保持 busy，確保完整 stop bit |
| 完成 | stop bit 維持 217 個 clock 後，busy 清零 |
| Counter | 計數 0～216；每 217 個 clock 移至下一 bit |
| Frame | `{stop=1, data[7:0], start=0}`，共 10 bits |
| Bit 時間 | 217 × 40 ns＝8.680 μs |
| Frame 時間 | 10 × 8.680 μs＝86.800 μs |

```text
Idle  Start   D0   D1   D2   D3   D4   D5   D6   D7   Stop  Idle
  1     0    ────────────低位先傳送─────────────        1      1
        │ 每格都是 217 個核心 clock │
```

`CLKS_PER_BIT` 是 elaboration parameter，使用至少 2。此版 FPGA 固定 217，沒有 baud 設定暫存器。單元測試可用 8 縮短時間；FPGA Top 測試仍使用實際的 217。

## 5．UART busy 與程式使用方式

| 存取 | UART 忙碌時的行為 |
| --- | --- |
| `LW UART_TX_STATUS` | 可以讀取 busy 快照 |
| 合法 `SW UART_TX_DATA` | req_ready 保持 0，CPU 等待；傳完才接受下一個 byte |
| 非法方向／strobe／offset | 回 error；不因 UART busy 無限等待 |

此版沒有 FIFO，寫入握手完成代表 UART **已接受** byte，不代表最後 stop bit 已送完。程式可以先輪詢 ready，再寫入；如果沒有輪詢，合法寫入仍會等待而不丟資料。

```asm
# x1 = UART base，x10 = 要送出的 byte
wait_ready:
    lw   x11,4(x1)
    andi x11,x11,1
    beq  x11,x0,wait_ready
    sw   x10,0(x1)
```

最後一個 byte 後，若要保證停止前傳送完畢，須再輪詢 ready。`FENCE` 只完成本 CPU 規格下的記憶體交易排序，**不會自動等待 UART 的最後 stop bit**。

Reset 會把 TX 拉回 idle high、取消 frame。接收端可能已收到部分資料，因此不能把 reset 當作「撤銷先前傳送」。

## 6．GPIO 架構與使用方式

| 項目 | 行為 |
| --- | --- |
| LED output | `SW GPIO_OUT` 擷取低 4-bit；直到下一次寫入或 reset |
| Readback | `LW GPIO_OUT` 回傳已保存的輸出值 |
| Switch input | `LW GPIO_IN` 回傳同步後的低 2-bit |
| 輸入同步 | `sw_meta` → `sw_sync`，兩級標記 `ASYNC_REG` 的 FF |
| 輸入延遲 | 開關改變後至少等待同步鏈及 MMIO 讀取延遲 |
| Debounce | 未加入；GPIO 回報同步的電位，不提供按下事件計數 |
| Reset | 輸出及輸入同步暫存器清零 |

```asm
# x2 = 0x20000200
addi x3,x0,10
sw   x3,0(x2)    # LED = 1010
lw   x4,0(x2)    # x4 = 10
lw   x9,4(x2)    # 讀 SW1/SW0
```

LED 的 bit 編號對應一般 LED0～3。`0xA＝1010` 表示 LED1／LED3 亮，LED0／LED2 滅；它是程式設定的圖案，不是硬體自動判斷成功的結果。

## 7．FPGA 接腳與 UART 接線

| 訊號 | 接腳／板上位置 | 用途 |
| --- | --- | --- |
| `clk125` | H16 | 125 MHz 來源 |
| `btn_reset` | D19／BTN0 | CPU reset |
| `sw[0]` | M20／SW0 | GPIO input bit 0 |
| `sw[1]` | M19／SW1 | GPIO input bit 1 |
| `led[0:3]` | R14、P14、N16、M14 | GPIO outputs |
| `uart_tx` | W14／Pmod B pin 1 | PL UART TX |
| GND | Pmod B pin 5 或 11 | 與轉接器共地 |

板上 PROG UART 的 USB-UART 接到 Zynq PS 的 MIO14／15；此版的 Fault-V 在 PL，所以使用 Pmod TX。接腳與 USB-UART 位置依據 [TUL PYNQ-Z2 Reference Manual](https://atta.szlcsc.com/upload/public/pdf/source/20190521/C393968_C7B875852931EF469F674C1E0E2AAA3E.pdf)。

使用 **3.3V TTL USB-to-UART** 轉接器：Pmod B pin 1 接轉接器 RX，Pmod GND 接轉接器 GND。此版本沒有 RX，所以不需要把轉接器 TX 接到 FPGA。板卡由原本供電方式供電，轉接器 VCC 不接入這條 UART 示範接線；不要使用 RS-232 電平介面。

電腦終端設定：115200 baud、8 data bits、no parity、1 stop bit、no flow control。沒有轉接器時，串列解碼 testbench 可驗證資料、順序及 start／stop bits。

## 8．時脈、reset 與約束

| 項目 | 規則 |
| --- | --- |
| MMCM | 延續 125 MHz → 25 MHz 與 BUFG 配置 |
| Reset | 按鈕與 lock 獨立同步鏈、約 10.49 ms 釋放等待、同步 rst 輸出 |
| BTN0 false path | 外部非同步 reset 宣告來源 |
| Switch false path | 僅 SW port → 第一級 `sw_meta` 的 D pin；第二級仍分析時序 |
| LED false path | 無外部同步接收暫存器 |
| UART output false path | 接收端沒有與核心共用的 capture clock；baud／bit 時間由功能模擬檢查 |
| 內部資料路徑 | CPU、UART counter、GPIO 及同步鏈後的資料路徑仍要通過 STA |

125 MHz 仍來自 PHY；其 reset 狀態會影響時脈供應。PL-only 設計仍保留 `ZPS7-1` 平台 warning，未把 PS 初始化或獨立上電啟動列為已驗證功能。

## 9．示範程式與預期結果

| 動作 | 預期 |
| --- | --- |
| 寫 GPIO＝5，讀回比較 | readback＝5；不一致走失敗路徑 |
| 讀取 GPIO_IN | 保存至資料 RAM `0x10000000` |
| 逐 byte 傳送 | `Fault-V OK`，接 CR＝0x0D、LF＝0x0A |
| 最後輪詢 ready | 最後 stop bit 完整送出後才繼續 |
| 寫 GPIO＝10 | LED 圖案 1010 |
| 寫 PROGRAM_STATUS＝1 | 回報成功 |
| EBREAK | CPU 依規格停止 |
| GPIO readback 失敗 | LED＝15、status＝2，然後 EBREAK |

訊息共 12 bytes：

```text
46 61 75 6C 74 2D 56 20 4F 4B 0D 0A
 F  a  u  l  t  -  V     O  K  CR LF
```

程式來源：`programs/peripheral_demo.S`；初始化影像：`programs/peripheral_demo.mem`。生成器以固定編碼產出 word，這個生成器不是完整 RISC-V assembler，也不替代 CPU 功能驗證。修改來源生成邏輯後以 `python build_demo.py` 更新影像，再重新建置 FPGA。

## 10．驗證內容與預期輸出

| Testbench | 檢查 |
| --- | --- |
| `tb_fault_v_io` | 16 筆交易；GPIO readback／遮罩、唯讀／唯寫與非法地址、回應 backpressure、UART busy write 等待、2 個串列 byte、reset 中止 frame |
| `tb_io_faults` | 8 種 CPU 周邊錯誤；fault 原因、PC、地址、請求數與無副作用 |
| `tb_fpga_top` | 真實 MMCM 模型與 217-cycle UART；兩次程式執行、24 個 byte、兩種開關值、BTN0 重跑 |
| `tb_reset` | 60 項 reset 規則 |
| ISA／程式 suite | 1372 次既有回歸，保持指令及 RAM／status 行為 |
| SoC／memory suites | 12 次程式與 16 筆記憶體交易 |

| CPU 錯誤案例 | 預期 |
| --- | --- |
| 讀 UART_TX_DATA | LOAD_ACCESS，已送出 1 筆交易 |
| 寫 UART_TX_STATUS | STORE_ACCESS，已送出 1 筆交易 |
| 寫 GPIO_IN | STORE_ACCESS，已送出 1 筆交易 |
| 讀 UART 非法 offset | LOAD_ACCESS，已送出 1 筆交易 |
| UART 的 SB | STORE_ACCESS，未送資料交易 |
| UART 的未對齊 LW | LOAD_ALIGN，未送資料交易 |
| GPIO_IN 的 LH | LOAD_ACCESS，未送資料交易 |
| GPIO 的未對齊 SH | STORE_ALIGN，未送資料交易 |

```text
ALL 16 IO TRANSACTIONS PASSED; 2 SERIAL BYTES PASSED
ALL 8 CPU IO FAULT CASES PASSED
PASS FPGA PERIPHERAL run=1 bytes=12 gpio=a input=1 status=1
PASS FPGA PERIPHERAL run=2 bytes=24 gpio=a input=2 status=1
ALL 2 FPGA PERIPHERAL PROGRAM RUNS PASSED; 24 UART BYTES PASSED
```

上述是驗收預期；實際測試紀錄獨立存放。testbench 使用數值 `8'h0D`／`8'h0A` 比對 CR／LF，避免不同字串跳脫解讀影響預期值。

## 11．Vivado 使用方式

使用此包完整 RTL，避免混入舊版 `fault_v_soc`／Top。先編譯 `fault_v_pkg.sv`；新增 `uart_tx.sv`、`fault_v_io.sv`。

在專案根目錄執行：

```powershell
& ./run_regression.ps1
& ./run_endpoint_regression.ps1
& ./run_xsim.ps1
& ./build_fpga.ps1
```

預設 Vivado 路徑 `C:\Xilinx\Vivado\2022.2\bin`，可使用 `-VivadoBin` 調整。GUI 的 Tcl Console 先 cd 到專案根目錄，再 `source create_project.tcl`；Design Top 為 `fault_v_fpga_top`。建立後依序執行 Synthesis、Implementation、Generate Bitstream。

| 交付物 | 用途 |
| --- | --- |
| `build/fault_v_fpga_top.bit` | PYNQ-Z2 的 FPGA 配置 |
| `build/fault_v_synth.dcp`／`fault_v_routed.dcp` | 綜合／繞線設計 |
| `logs/route_utilization.rpt` | 資源 |
| `logs/route_timing.rpt`／`clocks.rpt` | Setup、Hold、pulse-width、時脈及約束 |
| `logs/drc.rpt`／`methodology.rpt`／`cdc.rpt` | 結構、方法與同步規則 |
| `UART_GPIO_Verification.md` | 實際執行結果與限制 |

硬體管理員選對 Z2 後可使用 bitstream 配置 PL；BTN0 放開後程式重跑。實板仍要確認 PHY clock 與 Zynq 配置條件。實際 LED／串列終端結果只能在接板觀察後宣告。

## 12．驗收標準

| 項目 | 條件 |
| --- | --- |
| UART 格式 | Idle／start／8 bits／stop 順序與 bit 時間符合配置 |
| UART 資料 | byte 不遺失、不重複，busy 時等待，reset 行為明確 |
| GPIO | word 存取、readback、低位截斷、輸入同步及 reset 正確 |
| CPU 整合 | 有效周邊請求正常；非法／窄幅／未對齊請求正確停止 |
| 回應控制 | Backpressure 期間穩定，不重新觸發副作用 |
| CPU 回歸 | 既有 ISA、RAM、status、錯誤及程式測試持續通過 |
| FPGA | 資源不超量，繞線完整，Setup／Hold／pulse-width 通過，warning 明確列出 |
| 實板 | 配置、LED 控制、开關讀取、UART 接收與 reset 重跑有實際觀察紀錄 |

UART TX 與 GPIO 是可移植的同步 RTL；MMCM、BUFG、I/O 與 FPGA 記憶體初始化仍屬 FPGA 平台實作。ASIC 版要另行配置 clock／reset、I/O 電氣及記憶體方案。

## 13．完整 RTL、程式與約束

以下新增／修改來源與交付包一致。


### rtl/uart_tx.sv

```systemverilog
`timescale 1ns/1ps
module uart_tx #(parameter integer CLKS_PER_BIT=217)(
    input logic clk,rst,start,
    input logic [7:0] data,
    output logic tx,busy
);
    localparam integer CW=(CLKS_PER_BIT<=2)?1:$clog2(CLKS_PER_BIT);
    logic [CW-1:0] count;
    logic [3:0] bit_index;
    logic [9:0] frame;
    always_ff @(posedge clk) begin
        if (rst) begin
            tx<=1;busy<=0;count<=0;bit_index<=0;frame<=10'h3ff;
        end else if (!busy) begin
            tx<=1;
            if (start) begin
                frame<={1'b1,data,1'b0};
                tx<=0;busy<=1;count<=0;bit_index<=0;
            end
        end else if (count==CLKS_PER_BIT-1) begin
            count<=0;
            if (bit_index==9) begin tx<=1;busy<=0;end
            else begin bit_index<=bit_index+1'b1;tx<=frame[bit_index+1'b1];end
        end else count<=count+1'b1;
    end
endmodule

```

### rtl/fault_v_io.sv

```systemverilog
`timescale 1ns/1ps
module fault_v_io #(parameter integer UART_CLKS_PER_BIT=217)(
    input logic clk,rst,req_valid,req_write,
    input logic [31:0] req_addr,req_wdata,
    input logic [3:0] req_wstrb,
    output logic req_ready,rsp_valid,rsp_err,
    output logic [31:0] rsp_data,
    input logic rsp_ready,
    input logic [1:0] gpio_in,
    output logic [3:0] gpio_out,
    output logic uart_tx
);
    localparam logic [31:0] UART_DATA=32'h20000100,UART_STATUS=32'h20000104;
    localparam logic [31:0] GPIO_OUT=32'h20000200,GPIO_IN=32'h20000204;
    logic tx_busy;
    wire legal_tx_write=(req_addr==UART_DATA)&&req_write&&(req_wstrb==4'hf);
    wire fire=req_valid && req_ready;
    assign req_ready=!rst && !rsp_valid && !(legal_tx_write && tx_busy);
    uart_tx #(.CLKS_PER_BIT(UART_CLKS_PER_BIT)) u_tx(
        .clk(clk),.rst(rst),.start(fire && legal_tx_write),.data(req_wdata[7:0]),
        .tx(uart_tx),.busy(tx_busy));
    always_ff @(posedge clk) begin
        if (rst) begin gpio_out<=0;rsp_valid<=0;rsp_err<=0;rsp_data<=0;end
        else begin
            if (rsp_valid && rsp_ready) rsp_valid<=0;
            if (fire) begin
                rsp_valid<=1;rsp_err<=0;rsp_data<=0;
                if (req_write && req_wstrb!=4'hf) rsp_err<=1;
                else case(req_addr)
                    UART_DATA: if (!req_write) rsp_err<=1;
                    UART_STATUS: if (req_write) rsp_err<=1;
                                 else rsp_data<={30'b0,tx_busy,!tx_busy};
                    GPIO_OUT: begin
                        rsp_data<={28'b0,gpio_out};
                        if(req_write) gpio_out<=req_wdata[3:0];
                    end
                    GPIO_IN: if(req_write) rsp_err<=1;
                             else rsp_data<={30'b0,gpio_in};
                    default:rsp_err<=1;
                endcase
            end
        end
    end
endmodule

```

### rtl/fault_v_soc.sv

```systemverilog
`timescale 1ns/1ps
module fault_v_soc #(
    parameter string IMEM_FILE="",
    parameter integer IMEM_DELAY=1,
    parameter integer DMEM_DELAY=1,
    parameter integer UART_CLKS_PER_BIT=217
) (
    input logic clk,rst,
    input logic [1:0] gpio_in,
    output logic [3:0] gpio_out,
    output logic uart_tx,
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
    logic bus_pending,selected_io;
    logic ram_req_ready,ram_rsp_valid,ram_rsp_err,ram_rsp_ready;
    logic io_req_ready,io_rsp_valid,io_rsp_err,io_rsp_ready;
    logic [31:0] ram_rsp_data,io_rsp_data;
    wire io_hit=(dmem_req_addr[31:4]==28'h2000010) || (dmem_req_addr[31:4]==28'h2000020);
    wire ram_req_valid=dmem_req_valid && !bus_pending && !io_hit;
    wire io_req_valid=dmem_req_valid && !bus_pending && io_hit;
    assign dmem_req_ready=!rst && !bus_pending && (io_hit ? io_req_ready : ram_req_ready);
    assign dmem_rsp_valid=!rst && bus_pending && (selected_io ? io_rsp_valid : ram_rsp_valid);
    assign dmem_rsp_data=selected_io ? io_rsp_data : ram_rsp_data;
    assign dmem_rsp_err=selected_io ? io_rsp_err : ram_rsp_err;
    assign ram_rsp_ready=!rst && bus_pending && !selected_io && dmem_rsp_ready;
    assign io_rsp_ready=!rst && bus_pending && selected_io && dmem_rsp_ready;
    always_ff @(posedge clk)
        if(rst) begin bus_pending<=0;selected_io<=0;end
        else begin
            if(dmem_req_valid && dmem_req_ready) begin bus_pending<=1;selected_io<=io_hit;end
            if(dmem_rsp_valid && dmem_rsp_ready) bus_pending<=0;
        end
    fault_v_cpu u_cpu(.*);
    fault_v_memory #(.BASE_ADDR(0),.READ_ONLY(1),.INIT_FILE(IMEM_FILE),.RESPONSE_DELAY(IMEM_DELAY)) u_imem(
        .clk(clk),.rst(rst),.req_valid(imem_req_valid),.req_ready(imem_req_ready),
        .req_write(1'b0),.req_addr(imem_req_addr),.req_wdata(32'b0),.req_wstrb(4'b0),
        .rsp_valid(imem_rsp_valid),.rsp_ready(imem_rsp_ready),.rsp_data(imem_rsp_data),
        .rsp_err(imem_rsp_err),.program_status(unused_status));
    fault_v_memory #(.BASE_ADDR(32'h10000000),.WITH_STATUS(1),.RESPONSE_DELAY(DMEM_DELAY)) u_dmem(
        .clk(clk),.rst(rst),.req_valid(ram_req_valid),.req_ready(ram_req_ready),
        .req_write(dmem_req_write),.req_addr(dmem_req_addr),.req_wdata(dmem_req_wdata),.req_wstrb(dmem_req_wstrb),
        .rsp_valid(ram_rsp_valid),.rsp_ready(ram_rsp_ready),.rsp_data(ram_rsp_data),
        .rsp_err(ram_rsp_err),.program_status(program_status));
    fault_v_io #(.UART_CLKS_PER_BIT(UART_CLKS_PER_BIT)) u_io(
        .clk(clk),.rst(rst),.req_valid(io_req_valid),.req_ready(io_req_ready),
        .req_write(dmem_req_write),.req_addr(dmem_req_addr),.req_wdata(dmem_req_wdata),.req_wstrb(dmem_req_wstrb),
        .rsp_valid(io_rsp_valid),.rsp_ready(io_rsp_ready),.rsp_data(io_rsp_data),.rsp_err(io_rsp_err),
        .gpio_in(gpio_in),.gpio_out(gpio_out),.uart_tx(uart_tx));
endmodule

```

### board/fault_v_fpga_top.sv

```systemverilog
`timescale 1ns/1ps
module fault_v_fpga_top #(
    parameter string IMEM_FILE="peripheral_demo.mem",
    parameter integer RESET_HOLD_BITS=18,
    parameter integer UART_CLKS_PER_BIT=217
)(input wire clk125,btn_reset, input wire [1:0] sw,
  output wire [3:0] led,output wire uart_tx);
    wire clk,locked,rst;
    (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) logic [1:0] sw_meta=0,sw_sync=0;
    always_ff @(posedge clk)
        if(rst) begin sw_meta<=0;sw_sync<=0;end
        else begin sw_meta<=sw;sw_sync<=sw_meta;end
    fault_v_clock u_clock(.clk125(clk125),.clk(clk),.locked(locked));
    fault_v_reset #(.HOLD_BITS(RESET_HOLD_BITS)) u_reset(.*);
    fault_v_soc #(.IMEM_FILE(IMEM_FILE),.UART_CLKS_PER_BIT(UART_CLKS_PER_BIT)) u_soc(
        .clk(clk),.rst(rst),.gpio_in(sw_sync),.gpio_out(led),.uart_tx(uart_tx),
        .program_status(),.halted(),.halt_cause(),.fault_pc(),.fault_addr(),.pc(),.state(),
        .retire_valid(),.retire_rd_we(),.retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
endmodule

```

### board/fault_v_clock.sv

```systemverilog
`timescale 1ns/1ps
module fault_v_clock(input wire clk125, output wire clk, output wire locked);
    wire input_clock, feedback_raw, feedback, clock_raw;
    IBUF u_ibuf(.I(clk125), .O(input_clock));
    MMCME2_BASE #(
        .BANDWIDTH("OPTIMIZED"), .CLKIN1_PERIOD(8.0),
        .DIVCLK_DIVIDE(1), .CLKFBOUT_MULT_F(8.0),
        .CLKOUT0_DIVIDE_F(40.0), .STARTUP_WAIT("FALSE")
    ) u_mmcm (
        .CLKIN1(input_clock), .CLKFBIN(feedback), .RST(1'b0), .PWRDWN(1'b0),
        .CLKFBOUT(feedback_raw), .CLKOUT0(clock_raw), .LOCKED(locked),
        .CLKFBOUTB(), .CLKOUT0B(), .CLKOUT1(), .CLKOUT1B(),
        .CLKOUT2(), .CLKOUT2B(), .CLKOUT3(), .CLKOUT3B(),
        .CLKOUT4(), .CLKOUT5(), .CLKOUT6()
    );
    BUFG u_feedback(.I(feedback_raw), .O(feedback));
    BUFG u_clock(.I(clock_raw), .O(clk));
endmodule

```

### board/fault_v_reset.sv

```systemverilog
`timescale 1ns/1ps
module fault_v_reset #(parameter integer HOLD_BITS=18)(
    input wire clk, input wire locked, input wire btn_reset, output logic rst=1'b1
);
    // Asynchronous assertion; three clock edges synchronize release.
    // Every button bounce restarts the release delay (2^18 cycles ~= 10.49 ms).
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) logic [2:0] button_pipe=3'b111;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) logic [2:0] lock_pipe=3'b111;
    logic [HOLD_BITS-1:0] release_count='0;
    always_ff @(posedge clk or posedge btn_reset)
        if (btn_reset) button_pipe<=3'b111;
        else button_pipe<={button_pipe[1:0],1'b0};
    always_ff @(posedge clk or negedge locked)
        if (!locked) lock_pipe<=3'b111;
        else lock_pipe<={lock_pipe[1:0],1'b0};
    // A final synchronous register prevents asynchronous reset changes from
    // reaching BRAM enable pins between clock edges.
    always_ff @(posedge clk) begin
        if (button_pipe[2] || lock_pipe[2]) begin
            release_count<='0;
            rst<=1;
        end else begin
            if (!(&release_count)) release_count<=release_count+1'b1;
            rst<=!(&release_count);
        end
    end
endmodule

```

### constraints/pynq_z2.xdc

```tcl
set_property PACKAGE_PIN H16 [get_ports clk125]
set_property IOSTANDARD LVCMOS33 [get_ports clk125]
create_clock -name board_clk125 -period 8.000 [get_ports clk125]
set_property PACKAGE_PIN D19 [get_ports btn_reset]
set_property PACKAGE_PIN M20 [get_ports {sw[0]}]
set_property PACKAGE_PIN M19 [get_ports {sw[1]}]
set_property PACKAGE_PIN R14 [get_ports {led[0]}]
set_property PACKAGE_PIN P14 [get_ports {led[1]}]
set_property PACKAGE_PIN N16 [get_ports {led[2]}]
set_property PACKAGE_PIN M14 [get_ports {led[3]}]
# Pmod B pin 1: PL UART TX, connect to 3.3V USB-UART RX.
set_property PACKAGE_PIN W14 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports {btn_reset sw[*] led[*] uart_tx}]
set_false_path -from [get_ports btn_reset]
# Only first stages are asynchronous. Second-stage paths remain timed.
set sw_first_stage [get_pins -filter {REF_PIN_NAME == D} -of_objects [get_cells -hier -filter {NAME =~ *sw_meta_reg*}]]
set_false_path -from [get_ports {sw[*]}] -to $sw_first_stage
# LEDs and asynchronous UART receiver have no external shared capture clock.
set_false_path -to [get_ports {led[*] uart_tx}]

```

### programs/peripheral_demo.S

```asm
.section .text
.globl _start
_start:
    lui x1,0x20000
    addi x1,x1,256
    lui x2,0x20000
    addi x2,x2,512
    lui x7,0x20000
    addi x7,x7,0
    lui x8,0x10000
    addi x8,x8,0
    addi x3,x0,5
    sw x3,0(x2)
    lw x4,0(x2)
    bne x3,x4,fail
    lw x9,4(x2)
    sw x9,0(x8)
    addi x10,x0,70
wait_0:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_0
    sw x10,0(x1)
    addi x10,x0,97
wait_1:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_1
    sw x10,0(x1)
    addi x10,x0,117
wait_2:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_2
    sw x10,0(x1)
    addi x10,x0,108
wait_3:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_3
    sw x10,0(x1)
    addi x10,x0,116
wait_4:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_4
    sw x10,0(x1)
    addi x10,x0,45
wait_5:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_5
    sw x10,0(x1)
    addi x10,x0,86
wait_6:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_6
    sw x10,0(x1)
    addi x10,x0,32
wait_7:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_7
    sw x10,0(x1)
    addi x10,x0,79
wait_8:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_8
    sw x10,0(x1)
    addi x10,x0,75
wait_9:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_9
    sw x10,0(x1)
    addi x10,x0,13
wait_10:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_10
    sw x10,0(x1)
    addi x10,x0,10
wait_11:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,wait_11
    sw x10,0(x1)
drain:
    lw x11,4(x1)
    andi x11,x11,1
    beq x11,x0,drain
    addi x3,x0,10
    sw x3,0(x2)
    addi x3,x0,1
    sw x3,0(x7)
    ebreak
fail:
    addi x3,x0,15
    sw x3,0(x2)
    addi x3,x0,2
    sw x3,0(x7)
    ebreak

```

### verify/tb_fault_v_io.sv

```systemverilog
`timescale 1ns/1ps
module tb_fault_v_io;
    logic clk=0,rst=1,req_valid=0,req_write=0,rsp_ready=0;
    logic [31:0] req_addr=0,req_wdata=0;
    logic [3:0] req_wstrb=0;
    logic [1:0] gpio_in=2;
    wire req_ready,rsp_valid,rsp_err,uart_tx;
    wire [31:0] rsp_data;
    wire [3:0] gpio_out;
    integer tests=0,stalls=0,received=0;
    always #5 clk=~clk;
    fault_v_io #(.UART_CLKS_PER_BIT(8)) dut(.*);
    task automatic must(input logic good,input string text);
        if(good!==1'b1)$fatal(1,"FAIL IO: %s",text);
    endtask
    task automatic transaction(input logic wr,input logic[31:0] addr,data,
        input logic[3:0] mask,input logic error,input logic[31:0] expected);
        @(negedge clk);req_valid=1;req_write=wr;req_addr=addr;req_wdata=data;req_wstrb=mask;
        @(posedge clk);
        while(!req_ready) begin stalls++;@(posedge clk);end
        @(negedge clk);req_valid=0;
        must(rsp_valid && rsp_err==error && rsp_data===expected,"response");
        repeat(3) begin @(posedge clk);#1;
            must(rsp_valid && rsp_err==error && rsp_data===expected && !req_ready,"response held under backpressure");
        end
        @(negedge clk);rsp_ready=1;
        @(posedge clk);@(negedge clk);rsp_ready=0;
        must(!rsp_valid,"response consumed once");
        tests++;$display("PASS IO %0d addr=%h write=%b error=%b",tests,addr,wr,error);
    endtask
    task automatic receive_byte(input logic [7:0] expected);
        logic[7:0] actual;
        @(negedge uart_tx);#40;must(uart_tx==0,"start bit");
        #80;
        for(integer b=0;b<8;b++) begin actual[b]=uart_tx;#80;end
        must(uart_tx==1,"stop bit");must(actual==expected,"LSB first byte");
        received++;$display("PASS serial byte=%h",actual);
    endtask
    initial begin
        fork begin receive_byte(8'ha5);receive_byte(8'h3c);end join_none
        repeat(3) @(posedge clk);@(negedge clk);rst=0;
        transaction(0,32'h20000104,0,0,0,1);
        transaction(0,32'h20000200,0,0,0,0);
        transaction(1,32'h20000200,32'hfffffffA,15,0,0);
        must(gpio_out==10,"GPIO low four bits");
        transaction(0,32'h20000200,0,0,0,10);
        transaction(0,32'h20000204,0,0,0,2);
        transaction(1,32'h20000204,0,15,1,0);
        transaction(1,32'h20000200,0,1,1,0);must(gpio_out==10,"bad mask has no side effect");
        transaction(0,32'h20000100,0,0,1,0);
        transaction(1,32'h20000104,0,15,1,0);
        transaction(0,32'h20000108,0,0,1,0);
        transaction(0,32'h20000201,0,0,1,0);
        transaction(1,32'h20000100,8'ha5,15,0,0);
        transaction(0,32'h20000104,0,0,0,2);
        transaction(1,32'h20000100,8'h3c,15,0,0);
        must(stalls>0,"busy UART write stalls");
        wait(received==2);wait(!dut.tx_busy);
        transaction(0,32'h20000104,0,0,0,1);
        transaction(1,32'h20000100,8'h55,15,0,0);
        must(dut.tx_busy,"active frame before reset");
        @(negedge clk);rst=1;@(posedge clk);#1;
        must(uart_tx==1 && !dut.tx_busy && gpio_out==0 && !rsp_valid,"reset aborts frame and clears outputs");
        @(negedge clk);rst=0;repeat(12)@(posedge clk);
        must(uart_tx==1,"idle after reset");
        must(tests==16,"transaction count");
        $display("ALL 16 IO TRANSACTIONS PASSED; 2 SERIAL BYTES PASSED; stalls=%0d",stalls);$finish;
    end
    initial begin #20000;$fatal(1,"IO timeout");end
endmodule

```

### verify/tb_io_faults.sv

```systemverilog
`timescale 1ns/1ps
module tb_io_faults;
    import fault_v_pkg::*;
    logic clk=0;
    always #5 clk=~clk;
    logic [7:0] done=0;
    for(genvar g=0;g<8;g++)begin: cases
        localparam integer OFFSET=(g==0||g==4)?'h100:(g==1)?'h104:(g==2||g==6)?'h204:
            (g==3)?'h108:(g==5)?'h101:'h205;
        localparam integer CAUSE=(g==0||g==3||g==6)?6:(g==1||g==2||g==4)?7:(g==5)?4:5;
        localparam integer REQUESTS=(g<4)?1:0;
        localparam string IMAGE=(g==0)?"../programs/io_fault_0.mem":(g==1)?"../programs/io_fault_1.mem":
            (g==2)?"../programs/io_fault_2.mem":(g==3)?"../programs/io_fault_3.mem":
            (g==4)?"../programs/io_fault_4.mem":(g==5)?"../programs/io_fault_5.mem":
            (g==6)?"../programs/io_fault_6.mem":"../programs/io_fault_7.mem";
        logic rst=1;
        wire halted,uart_tx;
        wire [3:0] gpio_out;
        wire [31:0] fault_pc,fault_addr,program_status;
        halt_cause_t halt_cause;
        integer requests=0;
        fault_v_soc #(.IMEM_FILE(IMAGE),.UART_CLKS_PER_BIT(4)) dut(
            .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),
            .halted(halted),.halt_cause(halt_cause),.fault_pc(fault_pc),.fault_addr(fault_addr),
            .program_status(program_status),.pc(),.state(),.retire_valid(),.retire_rd_we(),
            .retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
        always @(posedge clk)if(!rst && dut.dmem_req_valid && dut.dmem_req_ready)requests++;
        initial begin
            repeat(3)@(posedge clk);@(negedge clk);rst=0;
            wait(halted);#1;
            if(halt_cause!=CAUSE || fault_pc!=8 || fault_addr!=32'h20000000+OFFSET || requests!=REQUESTS)
                $fatal(1,"FAIL IO fault %0d cause=%0d pc=%h addr=%h requests=%0d",g,halt_cause,fault_pc,fault_addr,requests);
            if(gpio_out!=0 || uart_tx!=1 || program_status!=0)$fatal(1,"Fault caused side effect");
            repeat(5)@(posedge clk);
            if(dut.dmem_req_valid)$fatal(1,"Request after halt");
            $display("PASS CPU IO fault %0d cause=%0d addr=%h requests=%0d",g,halt_cause,fault_addr,requests);
            done[g]=1;
        end
    end
    initial begin wait(&done);$display("ALL 8 CPU IO FAULT CASES PASSED");$finish;end
    initial begin #20000;$fatal(1,"CPU IO fault timeout");end
endmodule

```

### verify/tb_fpga_top.sv

```systemverilog
`timescale 1ns/1ps
module tb_fpga_top;
    import fault_v_pkg::*;
    logic clk125=0,btn_reset=0;
    logic [1:0] sw=1;
    wire [3:0] led;
    wire uart_tx;
    integer received=0,runs=0;
    realtime last_edge=0;
    string expected="Fault-V OK";
    always #4 clk125=~clk125;
    fault_v_fpga_top #(.IMEM_FILE("../programs/peripheral_demo.mem"),.RESET_HOLD_BITS(4)) dut(.*);
    task automatic must(input logic good,input string description);
        if(good!==1'b1)$fatal(1,"FAIL FPGA peripherals: %s",description);
    endtask
    always @(posedge dut.clk) begin
        if(dut.locked && last_edge>0)must(($realtime-last_edge>39.99)&&($realtime-last_edge<40.01),"25MHz");
        last_edge=$realtime;
    end
    initial forever begin
        logic [7:0] value;
        @(negedge uart_tx);#4340;
        must(uart_tx==0,"UART start bit middle");
        #8680;
        for(integer b=0;b<8;b++)begin value[b]=uart_tx;#8680;end
        must(uart_tx==1,"UART stop bit middle");
        if(received%12<10)must(value==expected.getc(received%12),"UART message text byte");
        else if(received%12==10)must(value==8'h0d,"UART CR byte");
        else must(value==8'h0a,"UART LF byte");
        received++;$display("PASS UART byte %0d: %h",received,value);
    end
    task automatic run_program(input integer round_id,input logic[1:0] switches);
        wait(!dut.rst);wait(dut.u_soc.halted);#1;
        must(dut.u_soc.program_status==1 && dut.u_soc.halt_cause==HALT_EBREAK,"CPU success");
        must(led==10,"program controls LED 0xA");
        must(dut.u_soc.u_dmem.mem[0]==switches,"switch read saved to RAM");
        must(received==round_id*12,"exactly twelve serial bytes per run, drained before halt");
        repeat(20)@(posedge dut.clk);
        must(!dut.u_soc.dmem_req_valid && uart_tx==1,"halt and UART idle");
        runs++;$display("PASS FPGA PERIPHERAL run=%0d bytes=%0d gpio=%h input=%h status=1",runs,received,led,switches);
    endtask
    initial begin
        run_program(1,1);
        #7 btn_reset=1;repeat(5)@(posedge dut.clk);#1;must(led==0,"reset clears GPIO");
        sw=2;#7 btn_reset=0;
        run_program(2,2);
        $display("ALL 2 FPGA PERIPHERAL PROGRAM RUNS PASSED; 24 UART BYTES PASSED");$finish;
    end
    initial begin #4000000;$fatal(1,"FPGA peripheral timeout");end
endmodule

```

### run_xsim.ps1

```powershell
param([string]$VivadoBin='C:\Xilinx\Vivado\2022.2\bin')
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force (Join-Path $PSScriptRoot 'sim'),(Join-Path $PSScriptRoot 'logs') | Out-Null
Push-Location (Join-Path $PSScriptRoot 'sim')
try {
    $sourceFiles=@('../rtl/fault_v_pkg.sv')
    $sourceFiles+=Get-ChildItem ../rtl/*.sv | Where-Object Name -ne 'fault_v_pkg.sv' | ForEach-Object {'../rtl/'+$_.Name}
    $sourceFiles+=Get-ChildItem ../board/*.sv | ForEach-Object {'../board/'+$_.Name}
    $sourceFiles+=@('../verify/tb_fpga_top.sv','../verify/tb_reset.sv','../verify/tb_fault_v_io.sv','../verify/tb_io_faults.sv')
    & (Join-Path $VivadoBin 'xvlog.bat') --sv @sourceFiles (Join-Path $VivadoBin '../data/verilog/src/glbl.v')
    if ($LASTEXITCODE -ne 0) {throw 'xvlog failed'}
    $tests=@(
        @{Top='tb_reset';Marker='ALL 60 RESET CHECKS PASSED'},
        @{Top='tb_fault_v_io';Marker='ALL 16 IO TRANSACTIONS PASSED'},
        @{Top='tb_io_faults';Marker='ALL 8 CPU IO FAULT CASES PASSED'},
        @{Top='tb_fpga_top';Marker='ALL 2 FPGA PERIPHERAL PROGRAM RUNS PASSED'}
    )
    foreach($test in $tests) {
        & (Join-Path $VivadoBin 'xelab.bat') $test.Top glbl -L unisims_ver -s $test.Top --debug typical --mt off
        if ($LASTEXITCODE -ne 0) {throw 'xelab failed'}
        & (Join-Path $VivadoBin 'xsim.bat') $test.Top -runall -log ($test.Top+'.log')
        if ($LASTEXITCODE -ne 0) {throw 'xsim failed'}
        $result=Get-Content ($test.Top+'.log') -Raw
        if ($result -match 'Fatal:' -or !$result.Contains($test.Marker)) {throw 'Missing PASS or failed simulation'}
        Copy-Item ($test.Top+'.log') ../logs/ -Force
    }
} finally {Pop-Location}

```

### create_project.tcl

```tcl
# Launch from package root in Vivado Tcl Console.
create_project fault_v_z2 build/project -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
add_files rtl/fault_v_pkg.sv
foreach f [glob rtl/*.sv] {
    if {[file tail $f] ne "fault_v_pkg.sv"} {add_files $f}
}
add_files [glob board/*.sv]
add_files programs/peripheral_demo.mem
add_files -fileset constrs_1 constraints/pynq_z2.xdc
set_property top fault_v_fpga_top [current_fileset]
update_compile_order -fileset sources_1


```

### build_fpga.tcl

```tcl
# Run with the working directory set to the package root.
set_param general.maxThreads 2
source create_project.tcl
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis did not complete"}
open_run synth_1
report_utilization -hierarchical -file logs/synth_utilization.rpt
write_checkpoint -force build/fault_v_synth.dcp
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation did not complete"}
open_run impl_1
report_utilization -file logs/route_utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file logs/route_timing.rpt
report_clock_utilization -file logs/clock_utilization.rpt
report_clocks -file logs/clocks.rpt
report_drc -file logs/drc.rpt
report_methodology -file logs/methodology.rpt
report_cdc -file logs/cdc.rpt
report_route_status -file logs/route_status.rpt
write_checkpoint -force build/fault_v_routed.dcp
file copy -force build/project/fault_v_z2.runs/impl_1/fault_v_fpga_top.bit build/fault_v_fpga_top.bit
set setup [get_timing_paths -delay_type max -max_paths 1]
set hold [get_timing_paths -delay_type min -max_paths 1]
if {[llength $setup]==0 || [llength $hold]==0} {error "No timed paths"}
if {[get_property SLACK $setup]<0 || [get_property SLACK $hold]<0} {error "Timing failed"}
if {[llength [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]]!=0} {error "Unresolved black boxes"}
source audit_design.tcl
puts "FPGA BUILD PASSED: routed design, nonnegative setup/hold slack, bitstream generated"

```

### audit_design.tcl

```tcl
# Current design must be routed. Keep all diagnostic severities unchanged.
report_route_status -file logs/route_status.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file logs/route_timing.rpt
report_drc -file logs/drc.rpt
report_methodology -file logs/methodology.rpt
set blackboxes [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]
set latches [get_cells -quiet -hier -filter {REF_NAME =~ LD*}]
if {[llength $blackboxes] || [llength $latches]} {error "Black box or latch present"}
foreach violation [get_drc_violations -quiet] {
    set severity [get_property SEVERITY $violation]
    if {$severity eq "Error" || $severity eq "Critical Warning"} {error "DRC failed: $violation"}
    # One board/platform warning is retained and described in the report.
    if {$severity eq "Warning" && ![string match "ZPS7-1*" $violation]} {
        error "Unexpected DRC warning: $violation"
    }
}
foreach type {max min} {
    set paths [get_timing_paths -delay_type $type -max_paths 1]
    if {[llength $paths]==0 || [get_property SLACK $paths]<0} {error "Timing failed: $type"}
}
set fh [open logs/route_timing.rpt r];set timing_report [read $fh];close $fh
if {![string match "*All user specified timing constraints are met.*" $timing_report]} {
    error "Timing summary includes violations"
}
foreach label {no_clock unconstrained_internal_endpoints generated_clocks loops latch_loops} {
    if {![regexp "checking $label \\(0\\)" $timing_report]} {error "Unexpected timing check: $label"}
}
if {![string match "*There are 0 input ports with no input delay specified.*" $timing_report]} {
    error "Unexpected unconstrained external input"
}
set switch_stages [get_cells -quiet -hier -filter {NAME =~ *sw_meta_reg* || NAME =~ *sw_sync_reg*}]
if {[llength [get_pins -hier -filter {NAME =~ *sw_meta_reg*/D}]]!=2} {
    error "Expected two switch first-stage D pins"
}
if {[llength $switch_stages]!=4} {error "Switch synchronization registers missing"}
foreach stage $switch_stages {
    if {![get_property ASYNC_REG $stage]} {error "Missing ASYNC_REG: $stage"}
}
puts "FPGA AUDIT PASSED: no latches/black boxes, timing met, only documented ZPS7-1 warning allowed"

```
