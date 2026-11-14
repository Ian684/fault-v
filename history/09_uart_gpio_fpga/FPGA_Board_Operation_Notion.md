# FPGA 下載與 LED 驗證

## 設計與預期行為

Fault-V 是 FPGA PL 中的自製 CPU。下載 `.bit` 後，指令記憶體包含 `peripheral_demo.mem`，CPU 從地址 0 執行程式。本示範程式最後寫入 GPIO 值 `0x5`，傳送 UART 訊息，回報狀態 1，然後 EBREAK 停止。

| 項目 | 意義／预期 |
| --- | --- |
| `.bit` | 設定 FPGA 的邏輯與初始記憶體內容 |
| LD0、LD2 | `0x5 = 4'b0101`，預期亮起 |
| LD1、LD3 | 預期熄滅 |
| BTN0 | Fault-V reset；持續按住時 GPIO 清零，放開後重新執行 |
| SW0、SW1 | 程式讀取並保存於 RAM；此示範不會把開關值直接映射到 LED |
| PS 系統 reset 按鈕 | 與本設計使用的 BTN0 不同，不能混用 |
| UART | 從 Pmod B pin 1 輸出；沒有外接轉接器時，不在電腦終端驗收 |

四個一般使用者 LED 與電源、DONE、RGB LED 是不同用途。LED 亮起只能提供有限的運作證據；此程式開始與結束都寫入 `0x5`，單看 LED 不能證明最後已成功 EBREAK，也不能證明 UART 每個字元正確。

## 接板子

1. 接線／調整跳線前先斷電。若使用 USB 供電，J9 選 USB；若使用外部供電，依板卡手冊選 REG 與相符電源。
2. 初次 JTAG 驗證可將 JP1 開機模式選 JTAG，避免其他開機程式重新設定 PL。不是寫入 Flash 的操作。
3. 使用可傳輸資料的 Micro-USB 線，接電腦與板子的 J8 USB-JTAG 埠。不要把 USB Host Type-A 埠當作 JTAG。
4. 開啟板子電源，確認電源狀態。

供電、JTAG、開機模式與 LED 定義依 [PYNQ-Z2 Reference Manual](https://atta.szlcsc.com/upload/public/pdf/source/20190521/C393968_C7B875852931EF469F674C1E0E2AAA3E.pdf)。

## Vivado 下載

| 順序 | 操作 |
| --- | --- |
| 1 | 開啟 Vivado，進入 Open Hardware Manager |
| 2 | 選 Open Target → Auto Connect |
| 3 | 確認找到 `xc7z020` 裝置；ARM DAP 不是要選的 FPGA 裝置 |
| 4 | 對 `xc7z020` 按右鍵，選 Program Device |
| 5 | Bitstream file 選本專案 `build/fault_v_fpga_top.bit` |
| 6 | 這版沒有 ILA，Debug probes file 留空 |
| 7 | 按 Program，確認下載成功，再觀察一般 LED |

完整 bitstream 路徑：

```text
<HOME>\Documents\Codex\2026-09-28\https-chatgpt-com-share-6aba66e3-8910\outputs\peripheral_z2\build\fault_v_fpga_top.bit
```

Vivado 2022.2 的連線入口參見 [AMD UG908](https://docs.amd.com/r/2022.2-English/ug908-vivado-programming-debugging/Opening-Hardware-Target-Connections)。

## 實板檢查與回報

| 操作 | 要記錄的現象 |
| --- | --- |
| 下載完成 | Vivado 是否顯示成功；LD0～LD3 各自是否亮起 |
| 持續按住 BTN0 | 四個一般 LED 是否熄滅 |
| 放開 BTN0 | LD0／LD2 是否再次亮起，LD1／LD3 是否保持熄滅 |
| 重複 10 次 BTN0 | 每次是否都能恢复相同輸出，有沒有某次不再啟動 |

未看到正確 LED 時，保留 Program Device 訊息與觀察結果，先區分 JTAG 下載失敗、時脈／reset 與程式行為。不要只憑 DONE 判定 CPU 已執行成功。

## 時脈與限制

本設計將 H16 的 125 MHz 轉為 25 MHz。125 MHz 來自 Ethernet PHY；PHY 被 reset 拉低時，時脈會停止。PL-only 建置仍保留 `ZPS7-1` DRC Warning，不能把電腦建置通過當成板上電源／PS 平台前置條件已證實。實板不啟動時須檢查這些條件；不應任意對 PS MIO 寫入未確認的暫存器值。

目前是 JTAG 暫時下載，未製作 Flash／SD 自動開機映像。修改 `.mem` 後必須重新建置 bitstream，單純重跑 RTL 模擬不會更新板上的程式。
