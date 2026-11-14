# CPU 穩定性、重置與 UART 網路輸出

這份筆記整理 CPU 在連續執行、記憶體等待、周邊操作與重置時的設計行為，以及 FPGA 實板的觀察方式。CPU 的 RV32I 指令語意不變；不同測試使用不同程式映像與平台設定。

| 測試版本 | Clock／UART 設定 | 用途與預期行為 |
| --- | --- | --- |
| RTL 壓力測試 | Testbench 提供 100 MHz；UART 64 clocks/bit | 有限次數執行，逐筆核對 RAM、GPIO、UART 與等待交易 |
| 實板連續執行 | 25 MHz；本程式不使用 UART | RAM 自我檢查持續循環，LED 5／A 交替 |
| 網路 UART 示範 | PS FCLK0 50 MHz；TX 434 clocks/bit | 輸出 Fault-V OK，最後 EBREAK；LED 固定為 5 |

三種版本的程式與時脈配置不可混用。網路示範正常結束後 LED 固定，不是連續測試的交替燈號。

## 1．RTL 連續執行與重置驗證

工作資料夾：`<HOME>/Documents/Codex/2026-09-28/https-chatgpt-com-share-6aba66e3-8910/outputs/peripheral_z2`。下列指令在此資料夾執行。

這組測試使用獨立的 `stress.mem`，保留 LED 示範程式。目的是檢查 CPU 反覆執行指令與存取周邊時，資料是否正確，以及等待與重置是否會造成重複交易。

| 檔案 | 用途 |
| --- | --- |
| `build_stress.py` | 產生組合語言與機器碼 |
| `programs/stress.S` | 人可閱讀的測試程式 |
| `programs/stress.mem` | CPU 指令記憶體載入的機器碼 |
| `verify/tb_stress.sv` | 外部測試、UART 解碼與交易監測 |
| `run_stress.ps1` | 產生映像、編譯、模擬並確認最終 PASS |

### 程式行為

| 工作 | 每次迴圈的動作 | 檢查方式 |
| --- | --- | --- |
| Word 記憶體 | `sw` 寫入計數值，再 `lw` 讀回 | 程式比較相同才繼續 |
| Byte 記憶體 | `sb` 寫入低 8-bit，再 `lbu` 讀回 | 與計數值低 8-bit 比較 |
| Halfword 記憶體 | `sh` 寫入，再 `lhu` 讀回 | 與計數值比較 |
| GPIO 輸出 | 寫入計數值，再讀回 GPIO | 與計數值低 4-bit 比較 |
| GPIO 輸入 | 讀取固定的兩個輸入位元 | 必須讀到 3 |
| UART | 直接寫入計數值低 8-bit | 外部解碼器逐 byte 比對 00～FF |
| 迴圈 | 計數從 0 到 1023 | 完整執行 1024 次 |

UART 寫入前刻意不輪詢 ready。如果 UART 忙碌，硬體必須讓 CPU 等待，等請求真正被接受才傳送一次。程式結束前輪詢 UART ready，確認最後一個 stop bit 已傳完，再寫入成功狀態 1 並執行 EBREAK。讀回比較失敗時寫入狀態 2。

### 測試配置與驗收

| 項目 | 配置／驗收條件 |
| --- | --- |
| 模擬時脈 | 10 ns 週期，由 testbench 直接提供給 SoC |
| UART 時序 | 每 bit 64 個 clock，8N1；為壓力測試加速配置 |
| 延遲配置 | 模式 0：IMEM／DMEM 延遲參數皆為 1；模式 1：分別為 7／11 |
| 完整執行 | 每模式重置後執行兩輪，共四輪 |
| 每輪 UART | 接受 1024 次寫入、實際解碼 1024 bytes，順序完全一致 |
| 每輪記憶體 | 3072 次 RAM 寫入，最後 word 0＝1023、word 1＝`0x03FF00FF` |
| 每輪 GPIO | 1024 次寫入，最後輸出 `0xF` |
| 交易監測 | 等待時請求與資料保持穩定；最多一筆未完成資料交易；完成時請求數等於回應數 |
| 等待路徑 | 每模式必須觀察到非零 stall cycles |
| 執行中重置 | 每模式分別在 RAM 回應等待中與 UART frame 中重置 |
| 重置後 | GPIO／狀態清零、UART 回到 idle、解除 halted，之後完整程式重新通過 |
| 停止後 | 不再產生取指或資料請求 |
| 模擬上限 | 30 ms 模擬時間，未完成就 `$fatal` |

RAM 不會因 reset 清空。已接受的寫入可能保留；重新開始的程式自行寫入並讀回，不能把 reset 當成交易回滾。中途中斷的 UART frame 不計入完整輪次的 1024 bytes。

### 執行方式

在此專案目錄的 PowerShell 執行：

```powershell
& .\run_stress.ps1
```

若新開的 PowerShell 視窗不允許腳本，先執行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

最終預期標記：

```
ALL 4 STRESS PROGRAM RUNS PASSED; 4096 UART BYTES PASSED; 4 MID-EXECUTION RESETS PASSED
```

### 適用範圍

這是有限長度的 RTL SoC 壓力測試，使用兩組固定記憶體延遲。沒有測試隨機延遲、所有可能的 reset 時刻或所有指令組合。直接提供的 SoC clock／reset 不涵蓋板上 clock/reset 電路，後者仍使用原有 Top 與 Reset 測試。此測試不建置 bitstream，不代表實板長時間穩定性、實際 UART 電氣品質或 ASIC 簽核已完成。

## 2．實板持續執行與記憶體自我檢查

工作資料夾：`<HOME>/Documents/Codex/2026-09-28/https-chatgpt-com-share-6aba66e3-8910/outputs/board_continuous`。下列指令在此資料夾執行。

### 工作方式

CPU 反覆掃描整個 16 KiB 資料 RAM。每一個地址寫入一個 32-bit 數值，再讀回並比較；4096 個 word 都相同才切換 LED。下一輪繼續使用遞增的測試值，32-bit 溢位時依整數指令規則截斷。程式不會正常結束，會持續執行直到 reset 或檢查失敗。

```
Reset → 初始化 → 寫入 RAM → 讀回比較 → 下一個 word
                               │              │
                               │              └→ 4096 words 都通過
                               │                         │
                               ▼                         ▼
                         不一致：LED=F               LED 5 ↔ A
                         狀態=2、EBREAK                狀態=1
                                                       │
                                                    軟體延遲
                                                       │
                                                    重新掃描
```

| 項目 | 規格 |
| --- | --- |
| 指令集 | 使用既有 RV32I 指令；不增加 CPU RTL 功能 |
| 記憶體範圍 | `0x10000000`～`0x10003FFF` |
| 每輪讀寫 | 4096 次 SW 與 4096 次 LW |
| 比較 | BNE；讀回與原值不同即進入錯誤路徑 |
| 正常 LED | `0x5` 與 `0xA` 交替，每次切換代表一輪掃描成功 |
| 軟體延遲 | x31 從 500000 遞減至 0，控制人可觀察的切換間隔 |
| 程式狀態 | 每輪通過寫入 1；資料比較失敗寫入 2 |
| 錯誤停止 | LED=`0xF`，之後 EBREAK；非標準機器模式 trap |
| Reset | GPIO 清零，程式從地址 0 重新開始；RAM 不清空 |
| UART／開關 | 此程式不使用，UART 保持 idle |

不同 CPU 錯誤不一定會到達軟體失敗路徑。若 LED 停在 5 或 A 而不再交替，也必須視為異常並進一步除錯，不能以「未全亮」推論沒有錯誤。

### 實板燈號

| 狀態 | LD0 | LD1 | LD2 | LD3 | 意義 |
| --- | --- | --- | --- | --- | --- |
| `0x5` | 亮 | 滅 | 亮 | 滅 | 一輪完整 RAM 檢查通過 |
| `0xA` | 滅 | 亮 | 滅 | 亮 | 下一輪完整 RAM 檢查通過 |
| `0xF` | 亮 | 亮 | 亮 | 亮 | 程式偵測到讀回不一致 |
| Reset | 滅 | 滅 | 滅 | 滅 | BTN0 按住，或重置釋放等待中 |

下載後先觀察兩組 LED 是否持續交替。按住 BTN0 時四顆熄滅，放開後應從第一輪重新開始並恢復交替。先觀察 1 分鐘，再進行 10 分鐘的持續運作檢查；若有異常，記錄時間、燈號，以及按 BTN0 後是否恢復。

這是 JTAG 暫時下載，斷電後不保留 FPGA 設定；尚未製作 Flash／SD 自動開機映像。下載會替換目前 PL 設計，原版檔案保留在 `peripheral_z2`。

### 檔案與指令

| 檔案 | 用途 |
| --- | --- |
| `build_program.py` | 產生測試程式 |
| `programs/board_loop.S` | 組合語言 |
| `programs/board_loop.mem` | 實板與模擬共用的指令映像 |
| `verify/tb_board_loop.sv` | 正常掃描、重置重啟與故障注入檢查 |
| `board/fault_v_fpga_top.sv` | 選用 board_loop.mem，其餘板上電路沿用原版 |
| `build/fault_v_fpga_top.bit` | 連續執行版本的 FPGA 設定檔 |

在本目錄執行：

```powershell
& .\run_sim.ps1
& .\build_fpga.ps1
```

模擬使用同一個實板 `.mem`，沒有縮短程式中的延遲計數。Testbench 直接提供 100 MHz SoC clock，檢查功能；實板使用原有 clock 電路產生 25 MHz。故障注入強制一次 load 回應為 `0xDEADBEEF`，確認軟體比較與失敗路徑有效；故障注入程式只在 testbench，未寫入 FPGA RTL。

### 驗證邊界

此程式是寫後立即讀的自我檢查，不是完整的 RAM March test、製造測試、指令相容性驗證或電源／溫度可靠度測試。LED 交替表示 CPU 完成指定工作；UART 實體輸出仍需要獨立驗證。實板時脈依賴 Ethernet PHY 的 125 MHz 輸出，原有 `ZPS7-1` 平台警告及時脈前置條件仍保留。

## 3．透過 Ethernet 顯示 UART 輸出

工作資料夾：`<HOME>/Documents/Codex/2026-09-28/https-chatgpt-com-share-6aba66e3-8910/outputs/network_bridge`。下列指令在此資料夾執行。

### 1．用途與資料路徑

電腦與 PYNQ-Z2 透過網路線連接。Fault-V 在 FPGA 可程式邏輯（PL）中執行程式並產生 UART TX 訊號；另一個硬體接收器把序列資料還原成字元，板上 ARM（PS）讀取後，透過 SSH 或 Jupyter 傳到電腦。

```
Fault-V CPU → MMIO UART TX → UART 序列訊號 → AXI UART Lite RX FIFO
                                                      ↓ AXI
                                                   ARM / Linux
                                                      ↓ Ethernet
                                               電腦：SSH 或 Jupyter
```

| 部分 | 工作 |
| --- | --- |
| Fault-V CPU | 執行自製 RISC-V 程式，透過 Store 寫入 UART 暫存器 |
| Fault-V UART TX | 產生 start、8 個資料位元及 stop bit |
| AXI UART Lite | 在 FPGA 內接收 UART 訊號，提供 16-byte 接收 FIFO |
| ARM / Linux | 透過 AXI 讀取 FIFO，檢查結果與 CPU 執行狀態 |
| Ethernet | 傳送已接收的字元與測試結果到電腦 |

此設計不需要 USB-to-UART 轉接器。接收器接在 FPGA 內部 UART 訊號上，因此涵蓋內部 UART 收發、ARM 讀取與網路輸出；Pmod 接腳、外部導線及電氣品質仍需另行驗證。

### 2．硬體設定

| 項目 | 設定 |
| --- | --- |
| 板卡 | PYNQ-Z2，xc7z020clg400-1 |
| Fault-V 核心 | 原有 32-bit 多周期 RV32I 核心，指令語意不變 |
| Clock | PS FCLK0，50 MHz；CPU、AXI 與接收器共用 |
| UART 格式 | 115200，8 個資料位元、無 parity、1 個 stop bit |
| Fault-V TX 分頻 | 434 clocks/bit；實際約 115207 baud |
| AXI UART Lite | 設定 115200；取樣分頻造成的實際值約 115741 baud |
| UART TX 外部接腳 | 同時送到 Pmod B pin 1，W14，LVCMOS33 |
| CPU 執行控制 | ARM 的 GPIO bit 0；0 保持 CPU reset，1 開始執行 |
| BTN0 | 重置 Fault-V；放開後重新執行，不重開 ARM Linux |
| 成功 LED | LD0、LD2 亮起，即 GPIO = 0x5 |
| 啟動方式 | SD 開機 Linux，再由 PYNQ 載入此 overlay |

50 MHz 與 UART TX 的 434 分頻必須一起使用；不可把此 wrapper 直接當成原本 25 MHz、217 分頻的版本。

### 3．ARM 可存取的暫存器

| ARM 位址 | 存取 | 功能 |
| --- | --- | --- |
| 0x42C00000 | Read | UART RX FIFO；讀取會取走一個 byte |
| 0x42C00008 | Read | UART status；bit 0 為 RX 有資料；bits 7:5 為 parity / frame / overrun 錯誤 |
| 0x42C0000C | Write | UART control；寫入 3 清空 TX 與 RX FIFO |
| 0x41200000 | Read / Write | 執行控制 bit 0：0 reset、1 run |
| 0x41200008 | Read | CPU debug status |

CPU debug status：bits 1:0 為程式狀態、bit 2 為 halted、bits 12:9 為 halt_cause，其餘位元為 0。示範正常結束時為 `0x00001205`：狀態 1、halted 1、halt_cause 9（EBREAK）。

以上是 ARM 的 AXI 位址。Fault-V 自己使用的 MMIO 配置仍是原有 `0x20000000` 狀態、`0x20000100` UART、`0x20000200` GPIO。

### 4．示範程式與驗收方式

示範程式輸出 `Fault-V OK\r\n`，共 12 bytes，設定 LED 為 0x5、程式狀態為 1，最後執行 EBREAK。

每次驗收依序執行：

1. ARM 設定 run = 0，保持 CPU reset。
2. 清空 UART FIFO。
3. ARM 設定 run = 1。
4. 讀取 UART status，有資料才取出 byte，並累積錯誤旗標。
5. 核對 12 bytes、無多餘資料、無 UART 錯誤，以及 debug status。
6. 重複三次，合計接收 36 bytes。

| 檢查 | 必須符合 |
| --- | --- |
| Clock | FCLK0 = 50 MHz |
| UART 字串 | 每次恰好 Fault-V OK 加 CR/LF |
| 接收錯誤 | parity、frame、overrun 均為 0 |
| CPU 狀態 | program_status = 1、halted = 1、halt_cause = 9 |
| FIFO | 完成後沒有多餘字元 |
| 重複執行 | 三次都符合以上條件 |

### 5．使用檔案

`fault_v_network.bit` 是 FPGA 設定檔；同名 `fault_v_network.hwh` 描述 clock、IP 與位址，必須配對保留。`receive_on_board.py` 在 Z2 執行，`deploy_and_receive.py` 在 Windows 上傳並透過 SSH 啟動測試。`Fault_V_Network.ipynb` 可在板子 Jupyter 網頁執行相同測試。

在 Windows 的本資料夾執行：

```powershell
python .\deploy_and_receive.py
```

此命令會建立新的板上示範資料夾、載入 overlay、執行三次驗收。需要 Python 的 paramiko 套件，且板子 IP、登入資料須符合 `remote_access.py`。

成功輸出的最後一行是：

```
ALL 3 NETWORK UART RUNS PASSED; 36 RECEIVED BYTES
```

載入 overlay 會替換目前的 FPGA 設計；SD 卡與 Linux 啟動設定不會被此腳本修改。斷電後此 overlay 不會自動保留，需要重新載入。

### 6．與 ASIC 的關係

PS、AXI UART Lite、AXI GPIO 與 Ethernet 是 FPGA 測試平台。Fault-V 的自製核心與 UART TX 仍是可移植 RTL；ASIC 的程式載入、外部 I/O、clock / reset 與測試介面需依晶片方案另行設計。