# Fault-V CPU 系統：驗證紀錄

- 日期：2026-10-07。
- 工具：Vivado 2022.2 XSim behavioral simulation。
- System DUT：`fault_v_soc`；Simulation Top：`tb_fault_v_soc`。
- Endpoint DUT：`fault_v_memory`；Simulation Top：`tb_fault_v_memory`。
- 編譯與兩個 elaboration 通過；交付腳本 `run_xsim.ps1` 已實際執行成功。

| 測試 | 結果 | 結束時間 |
| --- | --- | --- |
| 系統主程式、reset 重跑、錯誤及失敗程式 | ALL 12 SOC PROGRAM RUNS PASSED | 33207 ns |
| 記憶體 endpoint，含只讀實例 | ALL 16 MEMORY ENDPOINT TRANSACTIONS PASSED | 1490 ns |

兩個測試均正常 `$finish`，沒有 Fatal。

主程式先儲存十個 Fibonacci 值，透過 stack 保存外層返回位址，呼叫求和與加倍函式，得到 176，再驗證 subword Load／Store，回報 status＝1。三組 IMEM／DMEM 延遲分別為 1／1、2／3、3／5；各自 reset 後再次執行，六次均通過。每次主程式有 175 個正常 commit、33 筆資料交易，最後 EBREAK 在 0xCC。

另外五次硬體錯誤程式驗證非法指令、Load 未對齊、未映射 Store、超出指令記憶體範圍取指與未映射 MMIO。軟體失敗程式故意使用錯誤的總和比較值 177，正確回報 status＝2，並在 0x120 以 EBREAK 停止；這個預期失敗情境也算一筆通過的測試。

系統 testbench 不代替記憶體回應，只提供 clock／reset 並觀察結果。每次 commit 比對指令、PC、寫回與下一個 PC；每次停止比較全部 32 個暫存器及全部 4096 個資料 RAM words，包含 stack 與未使用區域，並驗證 request／response 計數、fault context、status 及停止後不繼續執行。

Endpoint 測試檢查完整及部分寫入、最後合法 word／下一個非法位址、未對齊直接請求、未配置 MMIO、狀態暫存器寬度、回應 backpressure 與 read-only 拒絕。三拍 backpressure 下 data／error／valid 保持，期間不可接受新請求。另有一笔已接受寫入後 reset 的測試：回應取消、status 清除，RAM 寫入仍保留。

本版記憶體在 request acceptance 更新 RAM／status，之後確認回應。RAM 在 reset 保留，模擬／FPGA 初始配置以 `initial`／`$readmemh` 載入；不同於先前 testbench 在成功 response 時更新、reset 初始化 byte array 的測試契約。技術筆記已明確說明這個改變。

CPU 的 11 個 RTL 檔案與前版相同，本次新增兩個系統模組。前版 CPU 功能驗證的 252 組結果沒有冒充本次重新執行的結果；本次重新執行的是系統與 endpoint 測試。RTL SHA-256 存於 `rtl_sha256.json`。

`.S`、`.mem` 與獨立指令語意預期模型由同一個結構化指令清單產生。編碼器與語意模型分開，不讀 DUT 訊號或複製 FSM 的週期安排。本次未使用 GNU／LLVM assembler、C toolchain 或正式 ISA compliance suite，有限案例也不代表全輸入证明。

這次完成 RTL 系統功能驗收，不包含 FPGA synthesis／implementation／時序／實板、UART／GPIO、動態程式載入或 ASIC memory macro／sign-off。`$readmemh` 初始化不能直接宣稱已完成 ASIC 的程式啟動方案。

證據：`logs/soc_results.log`、`logs/endpoint_results.log`。重現：`run_xsim.ps1`，或依技術筆記設定 Vivado Sources 與影像路徑後執行 `run all`。
