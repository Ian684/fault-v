# Fault-V Load／Store：驗證紀錄

- 日期：2026-10-07。
- 工具：Vivado 2022.2 XSim behavioral simulation。
- DUT：`fault_v_cpu`；Simulation Top：`tb_memory_cpu`。
- 編譯與 elaboration 通過。
- 125 個程式各執行兩種延遲，另有兩次 pending data transaction 時 reset，共 252 組情境。
- 最終結果：`ALL 252 MEMORY CPU SCENARIOS PASSED`。
- 正常 `$finish`：140656 ns，無 Fatal。
- 交付用 `run_xsim.ps1` 已實際重跑，成功檢查最終 PASS marker 並保存 log。

| 驗證項目 | 結果 |
| --- | --- |
| LB／LBU／LH／LHU／LW | 合法 lane、擴展與寫回通過 |
| SB／SH／SW | byte enable、資料排列及未寫入 byte 保留通過 |
| 資料相依 | 負偏移、Load 後運算／Store、rd＝base、x0 通過 |
| 記憶體迴圈 | 四筆 Store、四筆 Load，x5＝10，最終四個 word＝1、2、3、4 |
| 函式讀寫 | 跳躍、資料存取及返回路徑通過 |
| 對齊／非法編碼 | 停止且不發資料交易 |
| 失敗回應／未映射地址 | 正確停止，不 commit、不寫目的暫存器 |
| MMIO | 窄存取拒絕、對齊優先順序、word status stub 讀寫通過 |
| 握手等待 | 請求及 payload 穩定、一筆接受／一筆回應，全核心最多一筆 pending |
| reset | 已接受 Store／Load 後共同 reset，清掉 pending 並重跑通過 |
| 回歸 | 64 個既有整數／控制流程程式，兩種延遲均通過 |

新記憶體情境共 61 個。原本「Load／Store 尚未支援」兩個預期非法案例已從回歸移除，因為目前已正式接入這些路徑；其餘既有程式沿用原預期值。沒有把舊版本的預期錯誤行為當作新版驗收。

每次資料交易檢查位址、讀寫方向、wdata／wstrb、回應 word／error；每次 commit 檢查 InstrPC、機器碼、rd enable／資料及下一個 PC。每個情境停止後比較實際 32 個暫存器和 260 個模型 bytes，並確認停止後不繼續執行。

軟體模型以 byte array 表示記憶體，指令語意與機器碼生成分開，不讀 DUT，也不依賴 FSM 的週期安排。模型只涵蓋本測試使用的指令，未使用正式 ISA compliance suite。

測試 endpoint 在成功 Store 回應握手時更新資料，失敗 Store 不更新；reset 會取消 pending 並初始化模型記憶體。這些是本測試環境契約。CPU 不能回滾任意外部記憶體／MMIO 已發生的副作用，真實系統需明定回應完成與 reset 行為。

RTL 改動：新增 `load_extract.sv`、`store_align.sv`；CPU Top 新增 MDR、Load 写回來源、Store payload 與 Load／Store 類別支援。其餘八個 RTL 模組沿用上一整合版。

本次交付包含所有必要 RTL，支持規格列出的 40 個 RV32I 指令名稱與專案既定錯誤／停止行為；不宣稱正式相容性認證或標準 machine-mode。實際 16 KiB 記憶體、周邊、FPGA 綜合／時序／實板及 ASIC sign-off 尚未驗收。

原始證據：`logs/memory_cpu_results.log`。重現方式：`run_xsim.ps1` 或 Vivado Sources 設定後對 `tb_memory_cpu` 執行 `run all`。
