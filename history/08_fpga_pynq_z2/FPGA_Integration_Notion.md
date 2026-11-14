# Fault-V：PYNQ-Z2 FPGA 整合

## 1．用途與設計範圍

把已整合的 Fault-V CPU、指令記憶體、資料記憶體與程式狀態暫存器放進 PYNQ-Z2 的可程式邏輯（PL）。FPGA 以硬體電路執行預先載入的機器指令，板上的 LED 顯示是否停止、是否成功與是否發生錯誤。

| 項目 | 規格 |
| --- | --- |
| FPGA 板卡 | PYNQ-Z2 |
| Vivado 裝置 | `xc7z020clg400-1` |
| FPGA Design Top | `fault_v_fpga_top` |
| CPU 系統 | `fault_v_soc`，內含 `fault_v_cpu` 與兩個記憶體端點 |
| CPU | 32-bit、多周期、單指令依序完成、FSM 控制 |
| 指令語意 | 延續基礎 CPU；ECALL／EBREAK 與錯誤使用自訂停止介面 |
| 時脈 | 板上 125 MHz 經 MMCM 產生核心 25 MHz |
| 程式載入 | `integration.mem` 在綜合時納入 FPGA 初始化內容 |
| CPU reset | BTN0，高有效；獨立同步鏈、延遲釋放及同步 reset 輸出 |
| 結果輸出 | 四顆一般 LED；用途為觀察 CPU 狀態 |
| SoC 周邊 | 保留 `0x20000000` 的程式狀態暫存器 |
| ARM／DDR | 此設計沒有 PS block，也沒有使用板上 ARM 或 DDR |
| UART／GPIO 暫存器 | 尚未加入；LED 狀態接線不是可由程式操作的 GPIO 周邊 |

板卡型號、H16 時脈來源與一般 LED／按鈕接腳依據 [TUL PYNQ-Z2 Reference Manual](https://atta.szlcsc.com/upload/public/pdf/source/20190521/C393968_C7B875852931EF469F674C1E0E2AAA3E.pdf) 的 Clock Sources、LEDs／Buttons 章節。

## 2．整體架構

```text
H16：125 MHz ─→ IBUF ─→ MMCM ─→ BUFG ─→ 25 MHz core clock
                         │                     │
                         └─ LOCKED ─┐          │
BTN0：D19 ──────────────────────────┤          │
                                    ▼          │
                      reset 同步解除＋釋放延遲  │
                                    │ rst      │
                                    ▼          ▼
                           fault_v_fpga_top
                                    │
                             fault_v_soc
                       ┌────────────┼────────────┐
                       ▼            ▼            ▼
                  Fault-V CPU   16 KiB IMEM   16 KiB DMEM
                       │                         │
                       └──── 請求／回應握手 ──────┘
                                                │
                              status @ 0x20000000
                                    │
                heartbeat／halted／success／failure
                                    │
                               LED0～LED3
```

CPU 的 ALU、Decoder、Register File、PC、FSM 等仍在核心裡。新增的 FPGA 外層負責時脈、reset 與板卡接線；它不改變指令的計算結果。

## 3．檔案與責任

| 檔案／目錄 | 用途 |
| --- | --- |
| `rtl/` | 完整 CPU、SoC、記憶體及共用型別；使用此包整套來源 |
| `board/fault_v_clock.sv` | 125 MHz 輸入、MMCM、feedback BUFG 與核心 BUFG |
| `board/fault_v_reset.sv` | 按鈕／失鎖同步鏈、釋放延遲及同步 reset 輸出 |
| `board/fault_v_fpga_top.sv` | FPGA 最上層，連接時脈、reset、SoC 與 LED |
| `constraints/pynq_z2.xdc` | 實體接腳、電壓標準、時脈與非同步外部路徑規則 |
| `programs/integration.S` | 示範程式的組合語言來源 |
| `programs/integration.mem` | 4096 行、每行一個 32-bit word 的初始化影像 |
| `create_project.tcl` | 只建立 Vivado 專案，供 GUI 開啟操作 |
| `build_fpga.tcl`／`build_fpga.ps1` | 建立專案、綜合、實作、輸出報告與 bitstream |
| `run_xsim.ps1` | 板卡外層及 reset 模擬 |
| `run_regression.ps1` | 完整 ISA／程式回歸測試 |
| `run_endpoint_regression.ps1` | SoC 程式與記憶體端點回歸測試 |
| `logs/` | 模擬、資源、時序、DRC 等證據 |
| `FPGA_Integration_Verification.md` | 獨立保存實際執行結果及限制 |

不要同時加入以前版本的同名 RTL。`fault_v_pkg.sv` 要先於使用其型別的模組編譯。此包的 `fault_v_memory.sv` 已將 RAM 讀取與其他回應控制分離。

## 4．Clock 設計

| 項目 | 數值／元件 | 說明 |
| --- | --- | --- |
| 輸入 | 125 MHz，週期 8 ns | H16，`LVCMOS33` |
| 輸入 buffer | `IBUF` | 接收板上時脈 |
| MMCM | `MMCME2_BASE` | 7-series FPGA 時脈元件 |
| 輸入除頻 | 1 | `DIVCLK_DIVIDE` |
| Feedback 倍頻 | 8 | `CLKFBOUT_MULT_F` |
| VCO | 1000 MHz | 125 × 8 ÷ 1 |
| 輸出除頻 | 40 | `CLKOUT0_DIVIDE_F` |
| 核心 clock | 25 MHz，週期 40 ns | 1000 ÷ 40 |
| 全域 buffer | 兩個 `BUFG` | 一個 feedback，一個核心 clock |
| 鎖定訊號 | `locked` | 未鎖定時核心保持 reset |

25 MHz 是此配置的工作目標。可否運作須由實作後的 setup／hold 分析確認；不是 CPU 的最高頻率宣告。

XDC 只手動定義 125 MHz 輸入 clock，Vivado 依 MMCM 參數推導 25 MHz generated clock。不要另加一個與 MMCM 無關的同名 clock，也不要以一般暫存器翻轉訊號取代這個 clock tree。

**時脈供應條件：**125 MHz 來自 Ethernet PHY；PHY 的 `PHYRSTB` 被拉低時會停止供應。板卡操作時須保持這個來源可用，不能只憑成功產出 bitstream 就認定所有開機模式都已驗證。來源同上方 TUL 手冊。

## 5．Reset 設計

| 情況 | 外層行為 | 核心行為 |
| --- | --- | --- |
| FPGA 初始配置 | 兩組 pipeline 初值為 `111`，counter 為 0，rst 為 1 | 等待時脈與釋放條件 |
| MMCM 尚未鎖定／失鎖 | 非同步將 lock pipeline 設為 `111`，下一個可用邊緣更新 rst | 核心依 clock 上升緣同步 reset；clock 停止時不會執行 |
| BTN0 按下 | 非同步將 button pipeline 設為 `111`，下一個邊緣更新 rst | PC、FSM、暫存器與狀態依原規格同步 reset |
| BTN0 放開且 locked | 三個 clock 上升緣後 pipeline 解除 | 仍等待釋放 counter |
| 等待釋放 | 18-bit counter 數至全 1 | reset 保持有效 |
| 按鈕彈跳 | 再次按下會重啟解除流程及延遲 | 避免反覆短暫開始執行 |
| 穩定解除 | 約 10.49 ms 後釋放 | 從 PC＝0 重新執行 |

`ASYNC_REG` 與 `SHREG_EXTRACT="NO"` 標記兩組三級同步鏈，保留暫存器形式。BTN0 與 locked 不先經多輸入 LUT 合成非同步 reset，以免毛刺造成非預期重置。同步鏈後再以同步暫存器輸出 rst，避免非同步變化直接進入 BRAM enable。實體同步器降低亞穩態傳播機率；RTL 模擬無法量測實體亞穩態。

延遲為三級解除邊緣、`2^18−1` 次 counter 增加與一級同步輸出，約 10.49 ms。模擬把 `RESET_HOLD_BITS` 改為 4，只縮短等待時間；FPGA 預設仍為 18。核心看到有效 rst 後，在其上升緣執行 reset。

**RAM 不在 CPU reset 時清空。**重新配置 FPGA 才重新套用初始化內容；BTN0 重跑時由程式自行覆寫需要的資料。示範程式可以在資料 RAM 保留內容的情況下重跑。

## 6．FPGA 記憶體

| 項目 | 規格 |
| --- | --- |
| 指令位址 | `0x00000000～0x00003FFF`，16 KiB |
| 資料位址 | `0x10000000～0x10003FFF`，16 KiB |
| 狀態暫存器 | `0x20000000`，32-bit，獨立 MMIO |
| Word 排列 | 4096 × 32-bit；CPU 採 byte addressing、little-endian |
| RAM read | clock 上升緣取得資料，保存至無 reset 的 `ram_data` |
| Write | 請求接受時，以四個 byte enable 寫入 |
| Read during write | 回應保留寫入前的 word；CPU 不使用 Store 回應資料 |
| 協定控制 | `busy`、回應有效、錯誤、延遲與狀態維持原規則 |
| 非 RAM 回應 | `other_data` 保存 status 或 0；selector 選擇回應來源 |
| 初始化 | FPGA 配置時資料 RAM 為零，IMEM 從 `.mem` 載入 |

`ram_style="block"` 表達 BRAM 實作意圖，但實際資源須看綜合／實作報告。只有固定常數內容的指令 ROM，工具可能進一步折疊為邏輯；邏輯容量與最終 BRAM 數量不是同一件事。

把 `mem` 的 clocked read 放在獨立區塊，避免讓 BRAM read 暫存器同時承擔 reset、MMIO 或錯誤資料輸入。CPU 握手仍是接受請求後等待回應，沒有改成組合讀取。

FPGA BRAM 與初始化方式是此平台的實作。ASIC 版須另選 SRAM／ROM／啟動載入方案，不能把這些 FPGA 元件直接當作 ASIC 記憶體。

## 7．Top 介面與 LED

| 訊號 | 方向 | 接腳 | 規格／用途 |
| --- | --- | --- | --- |
| `clk125` | input | H16 | 125 MHz 時脈 |
| `btn_reset` | input | D19／BTN0 | 按下為 1，CPU reset |
| `led[0]` | output | R14／LED0 | reset 解除後顯示 heartbeat |
| `led[1]` | output | P14／LED1 | CPU 已停止 |
| `led[2]` | output | N16／LED2 | 已停止、原因 EBREAK、status＝1 |
| `led[3]` | output | M14／LED3 | 非成功停止，或 status 為其他非零碼 |

LED 為高有效。LED0 使用 24-bit counter 的 bit 23，25 MHz 下完整閃爍週期約 0.671 秒，程式停止後仍繼續閃爍。LED1～3 反映運算狀態，不是 ARM 的輸出。

| 觀察 | 意義 |
| --- | --- |
| reset 期間全部熄滅 | 尚未開始 |
| LED0 閃、LED1／2 亮、LED3 滅 | 示範程式成功停止 |
| LED1 與 LED3 亮、LED2 滅 | 非預期停止或錯誤 |
| LED3 亮、LED1 未亮 | 程式回報失敗碼，但尚未停止 |
| 全部長時間不亮 | 檢查供電、配置、125 MHz、BTN0、MMCM lock；不能單憑 LED 判定是哪個問題 |

## 8．Constraints 的範圍

| 約束 | 用途 | 不包含的承諾 |
| --- | --- | --- |
| `PACKAGE_PIN` | 指定真實 FPGA 接腳 | 不代替正確板卡選型 |
| `IOSTANDARD LVCMOS33` | 對應板卡訊號標準 | 不允許任意外部電壓 |
| `create_clock -period 8.000` | 分析 125 MHz 來源與衍生時脈 | 不等於核心跑 125 MHz |
| BTN0 false path | 按鈕是非同步 reset 宣告來源，沒有同步資料到達時間 | 不停用同步鏈後的核心 reset 分配時序 |
| LED output false path | LED 沒有外部 clocked receiving register | 不停用內部狀態暫存器與 LED 產生邏輯間的時序 |

檢查時序報告時，要確認內部暫存器有 clock、generated clock 正確，且沒有意外未約束的內部資料路徑。LED／按鈕的外部例外是有用途的介面規則，不應用來掩蓋 CPU critical path。

## 9．示範程式與預期結果

程式從 PC＝0 開始，執行 Fibonacci、迴圈、函式呼叫與返回、stack、不同資料寬度的記憶體操作，最後寫入 status＝1 並執行 EBREAK。

| 檢查項目 | 預期 |
| --- | --- |
| 資料 RAM 前 10 個 word | `0,1,1,2,3,5,8,13,21,34` |
| `0x10000030` | `0x123400EF` |
| `0x10000040` | `176`（`0x000000B0`） |
| `0x10003FFC` | `0x00000040`，stack 保存返回位址 |
| `program_status` | `1` |
| `halt_cause` | `HALT_EBREAK`，編碼 9 |
| `fault_pc` | `0x000000CC` |
| 正常完成指令數 | 175；最後 EBREAK 採停止行為，不計正常 retire |
| 資料請求數 | 33 |
| LED1～3 | LED1＝1、LED2＝1、LED3＝0 |

`.mem` 每行是完整 32-bit 指令 word，並不是每行一個 byte。更換程式時須同時更新來源與影像，重新綜合、實作及產出 bitstream。此配置沒有執行中的串列程式載入功能。

## 10．模擬方式與預期輸出

在 PowerShell 進入解壓後的專案根目錄，執行：

```powershell
& ./run_xsim.ps1
& ./run_regression.ps1
& ./run_endpoint_regression.ps1
```

預設使用 `C:\Xilinx\Vivado\2022.2\bin`。安裝路徑不同時，傳入 `-VivadoBin`。在 Vivado GUI 模擬板卡 Top 時，Simulation Top 是 `tb_fpga_top`，加入對應 testbench、`glbl.v` 與 `unisims_ver`；不要把 Design Top 改成 testbench。

| 模擬 | 檢查內容 | 最終預期訊息 |
| --- | --- | --- |
| `tb_reset` | 啟動、三級解除、delay、按鈕彈跳、lock loss | `ALL 60 RESET CHECKS PASSED` |
| `tb_fpga_top` | 真實 MMCM 模型、25 MHz、程式、LED、BTN0 重跑 | `ALL 2 FPGA TOP PROGRAM RUNS PASSED` |
| ISA／程式 suite | 全指令清單、邊界與錯誤、兩種等待延遲 | `ALL 1372 ISA AND PROGRAM RUNS PASSED` |
| SoC suite | 真實記憶體、程式、reset 保留 RAM | `ALL 12 SOC PROGRAM RUNS PASSED` |
| Memory endpoint | byte mask、ROM、MMIO、回應與錯誤 | `ALL 16 MEMORY ENDPOINT TRANSACTIONS PASSED` |

板卡 Top 的預期輸出：

```text
PASS FPGA run=1 commits=175 data=33 status=00000001 halt=9 pc=000000cc led=0110
PASS FPGA run=2 commits=175 data=33 status=00000001 halt=9 pc=000000cc led=0110
ALL 2 FPGA TOP PROGRAM RUNS PASSED
```

短版模擬的 LED0 尚未走到 bit 23 翻轉；LED0 的實體閃爍由板上觀察。上面是預期結果，實際跑出的紀錄存於獨立驗證文件及 logs。

## 11．建立 Vivado 專案與產出硬體

**自動建置：**

```powershell
& ./build_fpga.ps1
```

**GUI 操作：**在 Vivado Tcl Console 先 `cd` 到解壓後專案根目錄，再執行 `source create_project.tcl`。此方式只建立專案，接著在左側依序 Run Synthesis、Run Implementation、Generate Bitstream。已有專案時可開啟 `build/project/fault_v_z2.xpr`。

| 流程 | 做的事 | 要檢查的輸出 |
| --- | --- | --- |
| Synthesis | RTL 轉成 FPGA LUT／FF／RAM 等網表 | 利用率、BRAM 推導、latch／black box |
| Optimization | 去除冗餘、最佳化網表 | 不能有功能或結構錯誤 |
| Placement | 安排各個元件位置 | 元件合法、clock placement 合法 |
| Routing | 接通元件 | 無未完成／衝突繞線 |
| Timing | 使用實際線路延遲檢查 | setup、hold 與 pulse-width 條件 |
| DRC／Methodology | 檢查設計及約束 | 錯誤清除；warning 逐項理解 |
| Bitstream | 轉成 FPGA 配置資料 | `.bit` |

| 產物 | 用途 |
| --- | --- |
| `build/fault_v_fpga_top.bit` | 配置 PYNQ-Z2 的 PL |
| `build/fault_v_synth.dcp` | 綜合 checkpoint |
| `build/fault_v_routed.dcp` | 完成繞線 checkpoint |
| `logs/route_utilization.rpt` | FPGA 資源消耗 |
| `logs/route_timing.rpt` | setup／hold、clock、未約束路徑摘要 |
| `logs/clocks.rpt` | 時脈週期與 generated clock |
| `logs/drc.rpt` | 設計規則 |
| `logs/methodology.rpt`／`logs/cdc.rpt` | 方法與跨時脈／reset 檢查 |

建置腳本會重建 `build/project` 下的同名產出；不要把手動修改的專案設定當成唯一規格，來源與約束以包內檔案為準。

## 12．板上配置與操作

1. 用 PROG UART Micro-USB 接電腦，確認供電與 JTAG 可連線。
2. Vivado 開啟 Hardware Manager → Open Target → Auto Connect。
3. 確認目標為 Z2 的 `xc7z020`，選擇 Program Device。
4. 指定 `build/fault_v_fpga_top.bit`，配置 PL。
5. 等待 reset 延遲，觀察 LED0 heartbeat、LED1／LED2 亮、LED3 滅。
6. 按下 BTN0，LED 熄滅；放開後程式重新執行。

BTN0 是 CPU reset。板上 PROG／SRST 有不同的配置／系統重置用途，不要拿它們代替 BTN0 的重跑測試。此處使用 JTAG 配置流程；沒有建立 SD 卡或 Flash 的自動開機映像。

若沒有 heartbeat，先確認 125 MHz PHY clock 沒有被 PS 或其他開機軟體關閉。本設計沒有用 PS 軟體主動管理 PHY reset，因此必須在真實板卡上確認此條件。

## 13．資源與時序怎麼看

| 名稱 | 代表的硬體 | 判讀方式 |
| --- | --- | --- |
| LUT | 組合運算、解碼、多工等 | 與裝置可用量比較 |
| FF | PC、狀態、Register File 等 | 不等於組合語言的 32 個架構暫存器數量 |
| BRAM | FPGA 記憶體 | 看真實容量與已映射數量 |
| DSP | 專用運算元件 | 基礎整數 CPU 沒有要求乘法；以報告為準 |
| MMCM／BUFG | 時脈產生及分配 | 確認合法映射 |
| WNS／TNS | Setup slack／總負 slack | 要求 WNS ≥ 0、TNS＝0 |
| WHS／THS | Hold slack／總負 slack | 要求 WHS ≥ 0、THS＝0 |
| Pulse-width | 時脈脈衝寬度 | 也要符合條件 |

頻率提高代表 clock period 變短，可留給組合路徑的時間變少。此專案先以 40 ns 核心週期建立可實作基準；更換程式、RTL、裝置或時脈後要重新看報告。

## 14．驗收標準

| 層級 | 條件 |
| --- | --- |
| 功能 | FPGA 外層模擬輸出符合程式預期；重跑、reset 與 lock-loss 行為符合規格 |
| 回歸 | 修改後的完整 ISA、SoC、memory endpoint 測試通過 |
| 綜合 | 有可開啟的網表／DCP，無 latch、未解 black box，資源未超過裝置 |
| 實作 | 放置／繞線完整，時脈配置合法 |
| 時序 | Setup／Hold／Pulse-width 符合條件；內部資料路徑無意外未約束 |
| 規則 | DRC error 清除；warning 有明確原因與處理方式 |
| 交付 | RTL、影像、XDC、腳本、報告與 bitstream 可對應及重現 |
| 實板 | 成功配置、LED 結果正確、BTN0 可重跑；只能在實際觀察後宣告 |

RTL 模擬、FPGA 實作與實板觀察是三個不同的證據層級。FPGA bitstream 不等於 ASIC GDS；後續 ASIC 仍要處理製程元件庫、記憶體、I/O 與簽核流程。

### Zynq 平台警告的處理

此版本採 PL 設計，未加入 PS7 block。Vivado 的 `ZPS7-1` 會指出需要 PS7 才能提供正確的預設配置。這項 warning 保留原本嚴重程度，不降級、不隱藏，也不宣稱預設開機配置已完成。

CPU 的綜合、繞線、時序與 bitstream 可以分別驗收；實板操作仍要確認 PL 能配置、PHY clock 有供應，以及必要的 Zynq 平台狀態。若要整合 PS、由 PYNQ Linux 使用 overlay，或建立獨立上電開機流程，須加入正確 PS 設定及初始化，再重新建置與實測。

## 15．完整新增 RTL 與約束

以下來源與交付包一致；原有 CPU 模組在 `rtl/` 中。


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

### board/fault_v_fpga_top.sv

```systemverilog
`timescale 1ns/1ps
module fault_v_fpga_top #(
    parameter string IMEM_FILE="integration.mem",
    parameter integer RESET_HOLD_BITS=18
)(input wire clk125, input wire btn_reset, output wire [3:0] led);
    import fault_v_pkg::*;
    wire clk,locked,rst;
    logic [23:0] heartbeat=0;
    wire [31:0] program_status,fault_pc,fault_addr,pc;
    wire halted;
    halt_cause_t halt_cause;
    cpu_state_t state;
    fault_v_clock u_clock(.clk125(clk125),.clk(clk),.locked(locked));
    fault_v_reset #(.HOLD_BITS(RESET_HOLD_BITS)) u_reset(.*);
    fault_v_soc #(.IMEM_FILE(IMEM_FILE)) u_soc(
        .clk(clk),.rst(rst),.program_status(program_status),.halted(halted),
        .halt_cause(halt_cause),.fault_pc(fault_pc),.fault_addr(fault_addr),
        .pc(pc),.state(state),.retire_valid(),.retire_rd_we(),.retire_pc(),
        .retire_instruction(),.retire_rd_data(),.retire_rd_addr()
    );
    always_ff @(posedge clk)
        if (rst) heartbeat<=0;
        else heartbeat<=heartbeat+1'b1;
    wire success=halted && (halt_cause==HALT_EBREAK) && (program_status==32'd1);
    assign led[0]=!rst && heartbeat[23];
    assign led[1]=!rst && halted;
    assign led[2]=!rst && success;
    assign led[3]=!rst && ((halted && !success) ||
                          ((program_status!=0) && (program_status!=1)));
endmodule

```

### constraints/pynq_z2.xdc

```tcl
set_property PACKAGE_PIN H16 [get_ports clk125]
set_property IOSTANDARD LVCMOS33 [get_ports clk125]
create_clock -name board_clk125 -period 8.000 [get_ports clk125]
set_property PACKAGE_PIN D19 [get_ports btn_reset]
set_property IOSTANDARD LVCMOS33 [get_ports btn_reset]
set_property PACKAGE_PIN R14 [get_ports {led[0]}]
set_property PACKAGE_PIN P14 [get_ports {led[1]}]
set_property PACKAGE_PIN N16 [get_ports {led[2]}]
set_property PACKAGE_PIN M14 [get_ports {led[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[*]}]
# Button feeds asynchronous reset assertion only. Release is synchronized.
set_false_path -from [get_ports btn_reset]
# LEDs have no external clocked receiving device; internal paths stay timed.
set_false_path -to [get_ports {led[*]}]

```

### rtl/fault_v_memory.sv

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
    (* ram_style="block" *) logic [31:0] mem[0:WORDS-1];
    logic [31:0] ram_data,other_data;
    logic response_is_ram;
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
    assign rsp_data=response_is_ram ? ram_data : other_data;
    // BRAM read register has no reset or non-RAM data input.
    // Selector and protocol registers supply reset/status/error behavior.
    always_ff @(posedge clk) begin
        if (!rst && req_valid && req_ready && ram_hit && !(req_write && READ_ONLY)) begin
            ram_data<=mem[word_index];
            if (req_write && !READ_ONLY)
                for (integer lane=0;lane<4;lane=lane+1)
                    if (req_wstrb[lane]) mem[word_index][lane*8 +: 8]<=req_wdata[lane*8 +: 8];
        end
    end
    always_ff @(posedge clk) begin
        if (rst) begin
            busy<=0; remaining<=0; rsp_valid<=0; other_data<=0; response_is_ram<=0; rsp_err<=0;
            program_status<=0;
            // RAM contents intentionally survive reset. Accepted writes are not undone.
        end else begin
            if (req_valid && req_ready) begin
                busy<=1; remaining<=(RESPONSE_DELAY<1)?1:RESPONSE_DELAY;
                other_data<=0; response_is_ram<=0; rsp_err<=0;
                if (ram_hit) begin
                    if (req_write && READ_ONLY) rsp_err<=1;
                    else response_is_ram<=1;
                end else if (status_hit) begin
                    if (req_write && (req_wstrb!=4'b1111)) rsp_err<=1;
                    else begin
                        other_data<=program_status;
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

### verify/tb_reset.sv

```systemverilog
`timescale 1ns/1ps
module tb_reset;
    logic clk=0,locked=0,btn_reset=0;
    wire rst;
    always #20 clk=~clk;
    fault_v_reset #(.HOLD_BITS(4)) dut(.*);
    integer checks=0;
    task automatic check(input logic expected,input string description);
        if (rst!==expected) $fatal(1,"FAIL %s rst=%b",description,rst);
        checks++;
        $display("PASS reset %0d: %s",checks,description);
    endtask
    task automatic release_check;
        for(integer i=0;i<17;i++) begin @(posedge clk); #1;check(1,"release held");end
        repeat(2) @(posedge clk); #1;check(0,"release after 3 sync + 15 count + 1 output edges");
    endtask
    initial begin
        #1 check(1,"initial reset");
        #2 locked=1;
        release_check();
        #7 btn_reset=1;@(posedge clk);#1 check(1,"button synchronous core reset");
        @(negedge clk);btn_reset=0;
        repeat(6) @(posedge clk);
        #1 check(1,"delay during release");
        #2 btn_reset=1;@(posedge clk);#1 check(1,"bounce assertion");
        @(negedge clk);btn_reset=0;
        release_check();
        #7 locked=0;@(posedge clk);#1 check(1,"lock loss resets at next available edge");
        repeat(4) @(posedge clk);
        #1 check(1,"lock absent holds reset");
        @(negedge clk);locked=1;
        release_check();
        $display("ALL 60 RESET CHECKS PASSED");
        if(checks!=60) $fatal(1,"Unexpected check count %0d",checks);
        $finish;
    end
    initial begin #20000;$fatal(1,"reset timeout");end
endmodule

```

### verify/tb_fpga_top.sv

```systemverilog
`timescale 1ns/1ps
module tb_fpga_top;
    import fault_v_pkg::*;
    logic clk125=0,btn_reset=0;
    wire [3:0] led;
    always #4 clk125=~clk125;
    // Shortened release delay only; actual MMCM/BUFG models remain in the test.
    fault_v_fpga_top #(.IMEM_FILE("../programs/integration.mem"),.RESET_HOLD_BITS(4)) dut(.*);
    integer commits=0,transactions=0,runs=0;
    realtime last_edge=0;
    task automatic must(input logic good,input string description);
        if (good!==1'b1) $fatal(1,"FAIL %s",description);
    endtask
    always @(posedge dut.clk) begin
        if (dut.locked && last_edge>0) must(($realtime-last_edge>39.99)&&($realtime-last_edge<40.01),"25 MHz period");
        last_edge=$realtime;
        if (dut.rst) begin commits=0;transactions=0;end
        else begin
            if (dut.u_soc.retire_valid) commits=commits+1;
            if (dut.u_soc.dmem_req_valid && dut.u_soc.dmem_req_ready) transactions=transactions+1;
        end
    end
    task automatic execute_program;
        wait(!dut.rst);
        wait(dut.halted);
        #1;
        must(dut.program_status==1,"status success");
        must(dut.halt_cause==HALT_EBREAK,"expected EBREAK");
        must(dut.fault_pc==32'hcc,"stop address");
        must(commits==175,"175 retired instructions");
        must(transactions==33,"33 data transactions");
        must(led[3:1]==3'b011,"halt and success LEDs");
        must(dut.u_soc.u_dmem.mem[9]==34,"Fibonacci result");
        must(dut.u_soc.u_dmem.mem[12]==32'h123400ef,"byte/halfword writes");
        must(dut.u_soc.u_dmem.mem[16]==176,"function result");
        must(dut.u_soc.u_dmem.mem[4095]==32'h40,"last RAM word and stack");
        repeat(8) @(posedge dut.clk);
        must(commits==175 && transactions==33,"halt holds transactions and commits");
        runs=runs+1;
        $display("PASS FPGA run=%0d commits=%0d data=%0d status=%h halt=%0d pc=%h led=%b",runs,commits,transactions,dut.program_status,dut.halt_cause,dut.fault_pc,led);
    endtask
    initial begin
        execute_program();
        #7 btn_reset=1;
        @(posedge dut.clk);#1 must(dut.rst,"registered core reset assertion");
        repeat(5) @(posedge dut.clk);
        #1 must(dut.program_status==0 && !dut.halted && dut.pc==0,"core synchronous reset");
        #3 btn_reset=0;
        repeat(5) @(posedge dut.clk);
        #1 must(dut.rst,"release delay remains active");
        #2 btn_reset=1; #6 btn_reset=0;
        repeat(5) @(posedge dut.clk);
        #1 must(dut.rst,"button bounce restarts delay");
        execute_program();
        $display("ALL 2 FPGA TOP PROGRAM RUNS PASSED");
        $finish;
    end
    initial begin #200000; $fatal(1,"FPGA test timeout");end
endmodule

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
add_files programs/integration.mem
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
puts "FPGA AUDIT PASSED: no latches/black boxes, timing met, only documented ZPS7-1 warning allowed"

```
