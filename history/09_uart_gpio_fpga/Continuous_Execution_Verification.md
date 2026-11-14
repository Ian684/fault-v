# 連續執行驗證紀錄

驗證日期：2026-10-11（Asia/Taipei）。Vivado XSim 2022.2，執行 `run_stress.ps1`，程序退出碼 0。

| 模式 | 完整輪次 | 每輪迴圈 | 每輪 UART bytes | 每輪 RAM 寫入 | 每輪 GPIO 寫入 | 每輪 stall cycles | 每輪 retired instructions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0，延遲 1／1 | 2 | 1024 | 1024 | 3072 | 1024 | 501270 | 20585 |
| 1，延遲 7／11 | 2 | 1024 | 1024 | 3072 | 1024 | 317130 | 20543 |

共 4096 完整迴圈、4096 個 UART 解碼字元、12288 次 RAM 寫入、4096 次 GPIO 寫入。兩模式各通過 RAM 等待中重置、UART frame 中重置，共 4 次中途重置測試。stall 數為全部資料請求等待週期，不能直接當成 CPU 效能或加速倍數。

模擬於 13,148,175 ns 正常 `$finish`。證據：`logs/tb_stress.log`。

```text
ALL 4 STRESS PROGRAM RUNS PASSED; 4096 UART BYTES PASSED; 4 MID-EXECUTION RESETS PASSED
```

本次新增生成器、程式映像、testbench、執行腳本與文件，未修改 CPU／SoC／板上 RTL，未修改使用者 LED 示範程式。沒有重新合成或產生 bitstream，現有 `.bit` 仍不包含使用者剛修改的 LED 程式。原有 ZIP／manifest 為先前快照，未納入本次新增檔案。

測試限制見 `Continuous_Execution_Notion.md`。後續實板長時間運作：使用者於 2026-10-11 確認 board_continuous 連續測試版本正常；詳見 ../board_continuous/Verification_Report.md。此為另一個程式映像的實板證據，不等於本 stress.mem 已在板上執行。
