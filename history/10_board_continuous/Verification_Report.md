# 持續執行版本驗證紀錄

日期：2026-10-11（Asia/Taipei），Vivado/XSim 2022.2。

| 驗證 | 結果與證據 |
| --- | --- |
| RTL SoC 模擬 | 三次完整 4096-word RAM 掃描、reset 重新啟動、注入錯誤後 LED F／狀態 2／EBREAK 全部通過；`logs/tb_board_loop.log` |
| 模擬映像 | 与實板相同 board_loop.mem，未縮短軟體延遲；testbench 時脈 100 MHz，實板 25 MHz |
| 原有硬體 | 15 個 CPU／SoC RTL 檔案 SHA256 與 peripheral_z2 相同；Top 只更換默认程式名稱 |
| 合成／實體設計 | FPGA BUILD PASSED、FPGA AUDIT PASSED；`logs/build.log` |
| 時序 | WNS +26.094 ns、WHS +0.029 ns、WPWS +2.000 ns；TNS／THS 0 |
| DRC | 無 Error／Critical Warning；保留 ZPS7-1 Warning |
| 下載 | `xc7z020_1`，End of startup status HIGH、FAULTV_PROGRAM_COMPLETED，命令退出碼 0；`logs/hardware_program.log` |
| 實板 LED 與時間 | 使用者已確認 LED 交替、BTN0 反覆重置及長時間執行正常；2026-10-11 回報「長時間可以」。屬使用者觀察證據，未記錄精確持續時間或自動監測紀錄 |

Bitstream SHA256：`913E04AAF0416C4FC87F903E14B3CEE20CE5D910F12637F2076469E82B4584CB`。

仍有原有 reset 輸出宣告初始化警告與綜合的未使用輸入／最佳化警告；沒有聲稱建置完全無 Warning。XSim 對 task 的固定 expected 參數提出 sensitivity 提示；測試由 GPIO 實際變化喚醒，三輪掃描與故障注入均正常完成。未宣稱已完成所有時刻重置測試、完整 RAM 故障測試、實體 UART 或 ASIC 驗證。

原 LED 示範版本保留在 peripheral_z2，原有 ZIP／manifest 不包含本版本。此次只透過 JTAG 暫時下載，未寫入 Flash。
