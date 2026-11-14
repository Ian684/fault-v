# Fault-V UART／GPIO 驗證紀錄

日期：2026-10-10。工具：Vivado／XSim 2022.2，Windows。目標：PYNQ-Z2／xc7z020clg400-1。

**RTL／系統模擬與 FPGA 建置已驗證；尚未實板配置、接 UART 轉接器或量測串列波形。**使用者目前沒有轉接器，因此串列功能以 testbench 解碼驗證。板卡仍保留 PL-only 的 ZPS7-1 平台 warning，未宣稱獨立開機配置完成。

## 1．功能證據

| 驗證 | 實際結果 | 紀錄 |
| --- | --- | --- |
| ISA／程式回歸 | 1372 次通過；兩種等待模式皆為 40/40 指令名稱覆蓋 | `logs/verification_results.log` |
| 舊 SoC 程式回歸 | 12 次通過 | `logs/soc_results.log` |
| RAM／status 端點 | 16 筆交易通過 | `logs/endpoint_results.log` |
| UART／GPIO 端點 | 16 筆交易通過，2 個串列 byte 通過，busy 寫入實際等待 69 cycles | `logs/tb_fault_v_io.log` |
| CPU 周邊 fault | 8 案通過；原因、PC、地址、交易數與無副作用符合预期 | `logs/tb_io_faults.log` |
| Reset | 60 項通過 | `logs/tb_reset.log` |
| FPGA Top | 2 次程式執行、24 個 UART bytes 全部通過 | `logs/tb_fpga_top.log` |

Top 使用真正 MMCM／BUFG 的 UNISIM 模型與 UART 217 clocks/bit。兩輪都送出 `46 61 75 6C 74 2D 56 20 4F 4B 0D 0A`，最後 GPIO＝0xA、status＝1、halt＝EBREAK。第一輪 GPIO input＝1，第二輪＝2，兩者均正確保存到 RAM。BTN0 reset 後 GPIO 清零，再正常重跑。

端點測試檢查 start／stop bit、LSB-first 資料、busy 等待、回應 backpressure 穩定、錯誤存取無副作用，以及傳送中 reset 後 TX idle。單元測試使用 8 clocks/bit，Top 則驗證實際 FPGA 的 217 配置。

第一輪串列比對因 testbench 的 CR 字串跳脫解讀而失敗；改以明確 0x0D／0x0A 比對後通過，RTL 未因此改動。原始失敗紀錄保存於 `logs/first_serial_test.log`。

## 2．FPGA 結果

| 項目 | 結果 |
| --- | --- |
| Synthesis／Implementation | 成功，產生綜合及繞線 DCP |
| Bitstream | `build/fault_v_fpga_top.bit`，4,045,676 bytes |
| LUT | 1674／53200 |
| FF | 1427／106400 |
| BRAM | 7.5 個 tile；7 RAMB36＋1 RAMB18 |
| DSP | 0 |
| WNS／TNS | 26.344 ns／0 ns |
| WHS／THS | 0.106 ns／0 ns |
| WPWS | 2.000 ns |
| 無 clock／未約束的內部端點 | 0／0 |
| 無 delay 且無例外的外部 input | 0 |
| Methodology | 0 violations |
| DRC | 0 Error、0 Critical Warning；保留 ZPS7-1 warning |
| Black box／latch | 0／0 |
| 開關同步鏈 | 兩個第一級 D pin、四個 ASYNC_REG 暫存器，驗收腳本檢查 |

來源：`logs/build.log`、`route_utilization.rpt`、`route_timing.rpt`、`route_status.rpt`、`drc.rpt`、`methodology.rpt`。所有可繞線 nets 已完成，無 routing errors；setup／hold／pulse-width 符合指定約束。

初次 XDC 的名稱樣式沒有匹配到頂層 switch FF，造成 critical warning；已修正名稱、加入數量及 ASYNC_REG 檢查，重新建置。`logs/first_constraint_build.log` 保存修正前紀錄。最終約束只切斷 SW port 到第一級 D pin，未切斷同步鏈後的 CPU 資料路徑。

## 3．來源範圍與限制

新增 `uart_tx.sv`／`fault_v_io.sv`，修改 `fault_v_soc.sv` 的資料路由與外部介面、FPGA Top、XDC 及示範程式。其餘 12 個原有核心／記憶體 RTL 與前一版 FPGA 相同。此版是一套完整來源，不能只將新版 Top 與舊 SoC 混用。

UART 為 TX-only，無 FIFO、無接收、無硬體 flow control、無程式下載協定。開關只有同步，未提供機械 debounce 事件。GPIO LED 圖案是軟體產生，不能取代 fault 除錯介面的觀察。

沒有實板測試、post-route timing simulation、長時間硬體壓力測試或 ASIC 驗證。STA 與 RTL 模擬是本次的時序及功能證據。實板仍須確認 PHY 時脈與 Zynq 配置／初始化條件；既有 ZPS7-1 warning 沒有降級或隱藏。

SHA256 對應見 `manifest_sha256.csv`；bitstream、DCP、程式影像、RTL 與報告均在同一交付包中。

