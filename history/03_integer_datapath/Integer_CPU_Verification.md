# Fault-V 整數 CPU：驗證紀錄

- 執行日期：2026-10-07。
- 工具：Vivado 2022.2 XSim，SystemVerilog behavioral simulation。
- Top：`tb_fault_v_cpu`，DUT：`fault_v_cpu`。
- 編譯與 elaboration 通過。
- 結果：`ALL 11 INTEGER CPU PROGRAM SCENARIOS PASSED`。
- 結束時間：16346 ns，正常 `$finish`，沒有 Fatal。

四次完整程式各執行 37 次正常 commit，七次短程式各執行一次正常 commit，合計 155 次。每次停止前另取回一條停止／錯誤指令；取指失敗情境則回應錯誤。完整程式涵蓋 21 種整數運算、FENCE 及 EBREAK。測試逐次檢查 trace，並在各情境停止後比較全部 32 個實際暫存器。

| 情境 | 數量 | 結果 |
| --- | --- | --- |
| 三種取指延遲的相依程式 | 3 | 通過 |
| Load、Branch、Jump 未接入範圍 | 3 | 正確停止且無資料交易 |
| MUL、非法 shift 編碼 | 2 | 非法指令停止 |
| ECALL | 1 | 停止原因正確 |
| 取指失敗 | 1 | 保留已完成寫回與錯誤位址 |
| 已接受取指時 reset 再啟動 | 1 | 舊交易取消、完整程式重跑通過 |

首輪驗證發現測試预期值錯誤：`0x7FFFF000 + 0x7FF` 被寫成 `0x7FFFFFFF`。改用 `LUI 0x80000`、`ADDI -1`、`ADDI +1` 形成溢位邊界測試後，重新编譯並執行全部情境通過；此次修正没有改動 CPU RTL。

七個共用 RTL 模組沿用前次驗證版本。本次增加 CPU top、連續程式和 testbench，未把前次 controller harness 的結果冒充 CPU top 的驗證結果。

本紀錄只證明所列功能模擬案例。尚未驗收完整 RV32I、Branch／Jump／Load／Store top 整合、FPGA synthesis／implementation、時序與實板，亦未進行 ASIC sign-off。先前 controller 的額外 Vivado batch synthesis 曾因 `.Xil` 暫存目錄清理錯誤失敗，不能視為 synthesis 通過；本次交付不包含新的 synthesis 成功聲明。

原始證據：`logs/integer_cpu_results.log`。重現方式：`run_xsim.ps1`，或依技術筆記加入 Vivado Sources 後 `run all`。
