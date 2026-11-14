# CPU 連續執行與重置驗證

這組測試使用獨立的 `stress.mem`，保留 LED 示範程式。目的是檢查 CPU 反覆執行指令與存取周邊時，資料是否正確，以及等待與重置是否會造成重複交易。

| 檔案 | 用途 |
| --- | --- |
| `build_stress.py` | 產生組合語言與機器碼 |
| `programs/stress.S` | 人可閱讀的測試程式 |
| `programs/stress.mem` | CPU 指令記憶體載入的機器碼 |
| `verify/tb_stress.sv` | 外部測試、UART 解碼與交易監測 |
| `run_stress.ps1` | 產生映像、編譯、模擬並確認最終 PASS |

## 程式行為

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

## 測試配置與驗收

| 項目 | 配置／驗收條件 |
| --- | --- |
| 模擬時脈 | 10 ns 週期，由 testbench 直接提供給 SoC |
| UART 時序 | 每 bit 64 個 clock，8N1；為壓力測試加速配置 |
| 延遲配置 | 模式 0：IMEM／DMEM 延遲參數皆為 1；模式 1：分別為 7／11 |
| 完整執行 | 每模式重置後執行兩輪，共四輪 |
| 每轮 UART | 接受 1024 次寫入、實際解碼 1024 bytes，順序完全一致 |
| 每輪記憶體 | 3072 次 RAM 寫入，最後 word 0＝1023、word 1＝`0x03FF00FF` |
| 每輪 GPIO | 1024 次寫入，最後輸出 `0xF` |
| 交易監測 | 等待時請求與資料保持穩定；最多一筆未完成資料交易；完成時請求數等於回應數 |
| 等待路徑 | 每模式必須觀察到非零 stall cycles |
| 執行中重置 | 每模式分別在 RAM 回應等待中與 UART frame 中重置 |
| 重置後 | GPIO／狀態清零、UART 回到 idle、解除 halted，之後完整程式重新通過 |
| 停止後 | 不再產生取指或資料請求 |
| 模擬上限 | 30 ms 模擬時間，未完成就 `$fatal` |

RAM 不會因 reset 清空。已接受的寫入可能保留；重新開始的程式自行寫入並讀回，不能把 reset 當成交易回滾。中途中斷的 UART frame 不計入完整輪次的 1024 bytes。

## 執行方式

在此專案目錄的 PowerShell 執行：

```powershell
& .\run_stress.ps1
```

若新開的 PowerShell 視窗不允許腳本，先執行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

最終預期標記：

```text
ALL 4 STRESS PROGRAM RUNS PASSED; 4096 UART BYTES PASSED; 4 MID-EXECUTION RESETS PASSED
```

## 適用範圍

這是有限長度的 RTL SoC 壓力測試，使用兩組固定記憶體延遲。沒有測試隨機延遲、所有可能的 reset 時刻或所有指令組合。直接提供的 SoC clock／reset 不涵蓋板上 clock/reset 電路，後者仍使用原有 Top 與 Reset 測試。此測試不建置 bitstream，不代表實板長時間穩定性、實際 UART 電氣品質或 ASIC 簽核已完成。
