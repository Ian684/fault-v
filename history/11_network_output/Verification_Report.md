# Network UART Verification Report

實際執行日期：2026-10-11。板卡：PYNQ-Z2；PYNQ 2.5；Vivado / XSim 2022.2。

## 結果

| 項目 | 實測結果 | 證據 |
| --- | --- | --- |
| RTL payload 模擬 | 3 次執行、36 UART bytes；ARM run 控制及 BTN reset 通過 | logs/tb_payload.log |
| 基礎 CPU / SoC RTL | 15 個 RTL 檔案與 peripheral_z2 版本 SHA256 相同 | 檔案雜湊比較 |
| UART IP 設定 | HWH：C_BAUDRATE = 115200、C_S_AXI_ACLK_FREQ_HZ = 50000000 | fault_v_network.hwh |
| FPGA 建置 | 合成、佈線及 bitstream 產生成功 | logs/final_build.log |
| Setup | WNS = 6.895 ns、TNS = 0 | logs/timing.rpt |
| Hold | WHS = 0.044 ns、THS = 0 | logs/timing.rpt |
| Pulse width | WPWS = 9.020 ns，無失敗 endpoint | logs/timing.rpt |
| DRC | 0 violations | logs/drc.rpt |
| Methodology | 0 violations | logs/methodology.rpt |
| Routing | 4576 routable nets 全部完成，0 routing errors | logs/route.rpt |
| 實板 clock | ARM 讀到 FCLK0 = 50.0 MHz | logs/network_uart.log |
| 實板 UART / Ethernet | 三次各 12 bytes，完全符合 Fault-V OK + CR/LF | logs/network_uart.log |
| UART 錯誤 | 三次累積 parity / frame / overrun flags 均為 0；無多餘字元 | receive_on_board.py 驗收條件與成功紀錄 |
| CPU 結束 | 三次 status = 1、halted = 1、halt_cause = 9 | logs/network_uart.log |

Placed utilization：2409 LUT、2543 registers、7.5 個 BRAM tile、0 DSP。這包含 ARM 介接的測試平台邏輯，不能當成 ASIC 核心面積。

## 電腦實際收到的輸出

```text
ARM loaded Fault-V overlay; FCLK0=50.0 MHz
PASS NETWORK UART run=1 bytes=12 text='Fault-V OK\r\n' status=1 halt_cause=9
PASS NETWORK UART run=2 bytes=12 text='Fault-V OK\r\n' status=1 halt_cause=9
PASS NETWORK UART run=3 bytes=12 text='Fault-V OK\r\n' status=1 halt_cause=9
ALL 3 NETWORK UART RUNS PASSED; 36 RECEIVED BYTES
HOST RECEIVED BOARD OUTPUT VIA SSH/ETHERNET
```

載入位置：`/home/xilinx/jupyter_notebooks/fault_v_network_20261011_205512`。實際執行方式為 SSH / sudo Python，不是執行 Notebook；Notebook 已上傳供使用者重跑。

## 設定修正與保留警告

初版 25 MHz 的 AXI UART Lite 無法讓 115200 baud 的分頻誤差低於 IP 要求的 3%，設定曾被改成 110。該版本沒有載入板子。本次使用 50 MHz、Fault-V TX 分頻 434，核對最終 HWH 後才部署，並通過實板接收。

PS7 設定沿用板上正在正常運作的 PYNQ base.hwh。Vivado 對 DDR DQS_TO_CLK_DELAY_2 = -0.009、DELAY_3 = -0.033 保留 PSU-1 / PSU-2 critical warnings。沒有更動這些板級參數，也沒有執行 ps7_init 或重新初始化 DDR。本次 PL 功能測試通過，不代表已消除這兩個警告或驗證 DDR 在所有條件下的可靠度。

BD 41-702 提示使用者指定 clock 50 與傳播值 50.0；兩者相同，最終 HWH 與實板 clock 都已核對。Power 33-332 的 activity 假設警告仍在，因此不把 vectorless power estimate 當成已驗證功耗。

## 驗證範圍

實板結果涵蓋 Fault-V 執行、內部 UART 序列收發、AXI FIFO 讀取與 Ethernet/SSH 輸出。沒有 USB-to-UART 轉接器，所以未測外部 Pmod 電氣傳輸。沒有宣稱完成 ASIC 驗證或此網路示範版本的長時間壓力測試。另行載入的 board_continuous 版本已由使用者確認長時間執行正常；具體時間未記錄，證據見 ../board_continuous/Verification_Report.md。

載入後板子執行示範程式，停在 EBREAK；設計設定 GPIO = 5。此時 LED 靜態顯示，與先前 continuous image 的交替閃爍用途不同。

## 交付檔案 SHA256

- fault_v_network.bit：`6C7130C28EAC8F079B5D4EF399656F6F445EB7DF4C558B9B28AACF8DE632300C`
- fault_v_network.hwh：`F2424173ABD241C78DB187A3327B0AC7967E3D19BC74446C308A58986191F913`
