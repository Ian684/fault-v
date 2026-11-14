# Fault-V：透過 Ethernet 顯示 UART 輸出

## 1．用途與資料路徑

電腦與 PYNQ-Z2 透過網路線連接。Fault-V 在 FPGA 可程式邏輯（PL）中執行程式並產生 UART TX 訊號；另一個硬體接收器把序列資料還原成字元，板上 ARM（PS）讀取後，透過 SSH 或 Jupyter 傳到電腦。

```text
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

## 2．硬體設定

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

## 3．ARM 可存取的暫存器

| ARM 位址 | 存取 | 功能 |
| --- | --- | --- |
| 0x42C00000 | Read | UART RX FIFO；讀取會取走一個 byte |
| 0x42C00008 | Read | UART status；bit 0 為 RX 有資料；bits 7:5 為 parity / frame / overrun 錯誤 |
| 0x42C0000C | Write | UART control；寫入 3 清空 TX 與 RX FIFO |
| 0x41200000 | Read / Write | 執行控制 bit 0：0 reset、1 run |
| 0x41200008 | Read | CPU debug status |

CPU debug status：bits 1:0 為程式狀態、bit 2 為 halted、bits 12:9 為 halt_cause，其餘位元為 0。示範正常結束時為 `0x00001205`：狀態 1、halted 1、halt_cause 9（EBREAK）。

以上是 ARM 的 AXI 位址。Fault-V 自己使用的 MMIO 配置仍是原有 `0x20000000` 狀態、`0x20000100` UART、`0x20000200` GPIO。

## 4．示範程式與驗收方式

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

## 5．使用檔案

`fault_v_network.bit` 是 FPGA 設定檔；同名 `fault_v_network.hwh` 描述 clock、IP 與位址，必須配對保留。`receive_on_board.py` 在 Z2 執行，`deploy_and_receive.py` 在 Windows 上傳並透過 SSH 啟動測試。`Fault_V_Network.ipynb` 可在板子 Jupyter 網頁執行相同測試。

在 Windows 的本資料夾執行：

```powershell
python .\deploy_and_receive.py
```

此命令會建立新的板上示範資料夾、載入 overlay、執行三次驗收。需要 Python 的 paramiko 套件，且板子 IP、登入資料須符合 `remote_access.py`。

成功輸出的最後一行是：

```text
ALL 3 NETWORK UART RUNS PASSED; 36 RECEIVED BYTES
```

載入 overlay 會替換目前的 FPGA 設計；SD 卡與 Linux 啟動設定不會被此腳本修改。斷電後此 overlay 不會自動保留，需要重新載入。

## 6．與 ASIC 的關係

PS、AXI UART Lite、AXI GPIO 與 Ethernet 是 FPGA 測試平台。Fault-V 的自製核心與 UART TX 仍是可移植 RTL；ASIC 的程式載入、外部 I/O、clock / reset 與測試介面需依晶片方案另行設計。
