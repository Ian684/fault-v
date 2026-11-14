# Fault-V Branch／Jump：驗證紀錄

- 日期：2026-10-07。
- 工具：Vivado 2022.2 XSim，behavioral simulation。
- DUT：`fault_v_cpu`；Simulation Top：`tb_branch_cpu`。
- 编譯與 elaboration 通過。
- 66 個程式，各執行兩種取指延遲；另含兩次 commit 前 reset 再重跑，共 134 組情境。
- 結果：`ALL 134 BRANCH CPU SCENARIOS PASSED`。
- 正常 `$finish`：69626 ns，無 Fatal。

| 驗證範圍 | 結果 |
| --- | --- |
| BEQ／BNE／BLT／BGE／BLTU／BGEU | 成立、不成立、相等、負數與 signed 邊界通過 |
| Branch 未對齊目標 | 成立時停止；不成立時正常前進 |
| 反向迴圈與函式返回 | x3＝25，正常 commit 22 次，取指 23 次 |
| 巢狀呼叫 | x10＝5，x5＝4，x1＝0x10，返回路徑正確 |
| JAL | 正／負位移、x0、link、對齊與目標取指錯誤通過 |
| JALR | bit 0 清除、bit 1 對齊、負立即數、rd＝rs1、rd＝x0 通過 |
| 立即數／位移邊界 | B、J、I 位移的代表邊界案例通過 |
| 非法編碼與未接入 Load／Store | 停止原因與無副作用行為通過 |
| 原整數程式、ECALL、取指失敗 | 回歸通過 |
| BR_COMMIT／JUMP_COMMIT 前 reset | 取消該次動作，清狀態後重跑通過 |

每條正常完成指令都檢查機器碼、InstrPC、rd enable／編號／資料，以及下一個 PC。所有情境停止時，檢查全部 32 個實際暫存器與独立預期模型，並確認停止後不繼續執行。reset 情境由核心與測試記憶體共用 reset。

預期資料由 `build_cases.py` 的指令語意模型與編碼器產生；模型不讀 DUT，不依賴 FSM 的週期安排。既有整數回歸程式保留固定常數預期值。這是專案測試模型，未使用正式 ISA compliance suite，不能視為全輸入證明或完整 RV32I 相容性認證。

首輪的一個案例名稱写成「JALR high aligned address fetch fails」，但輸入 0xFFFFFFFF 清 bit 0 後是 0xFFFFFFFE，實際為未對齊。將輸入修正為 0xFFFFFFFD，目標變為 0xFFFFFFFC，重新驗證其正常跳躍及後續取指失敗；沒有為了讓案例通過而改變 CPU 對齊規則。

RTL 改動：新增 `branch_compare.sv`；更新 CPU top 的 BranchTaken 保存、JALR 目標處理、link 寫回 MUX 與指令類別允許範圍。其他七個共用模組沿用上一版。

本次僅驗收 RTL 功能模擬。Load／Store 尚未接入；沒有新增 FPGA synthesis／implementation、板上測試或 ASIC sign-off 成功聲明。紀錄與技術筆記分開保存。

證據：`logs/branch_cpu_results.log`。重現方式：PowerShell 執行 `run_xsim.ps1`，或依技術筆記設定 Vivado Sources 與 Simulation Top 後 `run all`。
