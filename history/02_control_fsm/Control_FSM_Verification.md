# Fault-V｜Control FSM 驗證紀錄

工具：Vivado 2022.2 XSim；驗證日期：2026-10-05（台灣）。驗證在獨立 control_fsm 資料夾執行，Downloads/fault-V 原專案未被修改。

**① 功能模擬結果**

| 執行紀錄 | 完成訊息 | 結束時間 |
| --- | --- | --- |
| control_fsm_results.log | `ALL 92 CONTROL FSM SCENARIOS PASSED (5626 checks)` | 9836 ns |
| control_path_results.log | `ALL 76 CONTROL PATH CASES PASSED` | 11051 ns |
| tb_decoder_results.log | `ALL 33943 DECODER CHECKS PASSED` | 33943 ns |
| tb_decode_path_results.log | `ALL 33 DECODE PATH CASES PASSED` | 330 ns |
| tb_alu_results.log | `ALL 20 ALU TESTS PASSED` | 200 ns |
| tb_imm_gen_results.log | `ALL 21 IMM TESTS PASSED` | 210 ns |
| tb_regfile_results.log | `ALL 104 REGFILE CHECKS PASSED` | 1371 ns |
| tb_pc_reg_results.log | `ALL 17 PC CHECKS PASSED` | 146 ns |
| tb_pc_path_results.log | `ALL 13 PC PATH CASES PASSED` | 660 ns |

控制器單元測試包含 92 個情境、5,626 次明確檢查；整合測試包含 76 個案例。各測試以完成標記及無 Fatal／FAIL／TIMEOUT 判定，不能只用 xsim 程序退出碼判断。

**② 驗證內容與實際界線**

單元測試核對狀態／控制輸出、握手追蹤、0～3 拍請求與回應等待、錯誤停止、原始 fault_addr、所有 15 狀態的 reset，以及接受交易後的 reset。

整合測試使用真正 Decoder、ALU、imm_gen、RF、PC、FSM；testbench 接出中間暫存器與資料處理，透過固定指令與記憶體替身驗證 40 種基本指令名稱、六種分支的正反條件、跳躍、Load 擴展、Store mask、MMIO 規則與錯誤。額外確認跳躍後的目標取指失敗不回復已提交返回位址。

回歸測試使用更新後 package 重新編譯所有既有模組與 testbench。

尚未進行所有資料組合／形式驗證、HALT_INTERNAL 硬體故障注入、完整程式執行、真實 SRAM／UART／GPIO 互連、實板與 ASIC 驗證。外部共同 reset／無舊回應的約定仍需在正式互連中落實。

**③ 綜合檢查**

功能模擬全部通過。額外執行 control_fsm 的 xc7z020clg400-1 out-of-context 綜合時，Vivado 已進入網表生成並輸出 cell 統計，但最後清理 .Xil/.../realtime/tmp 時報「no such file or directory」，導致 synth_design 回傳失敗。嘗試較短工作路徑與預建暫存目錄後仍遇到同一類工具檔案系統問題。

因此本次不記錄完整綜合通過、零 latch 檢查通過或可用 synthesis checkpoint；中途的 73 個 FDRE 等統計不能替代最後驗收。synthesis.log 保留失敗與查詢可用設計的診斷輸出。提供的 check_synthesis.tcl 是正常綜合與結構檢查腳本，遇到失敗會停止，不會忽略錯誤當成通過。

此項不影響已完成的 XSim 功能測試。FPGA 完整時序、實板與 ASIC 驗證仍需在各自整合環境執行。

**④ 重現與檔案一致性**

在解壓後的資料夾可使用 run_xsim.ps1；預設工具位置 C:/Xilinx/Vivado/2022.2/bin，可透過 -VivadoBin 指定其他安裝位置。只重跑既有模組可加 -RegressionOnly。

技術筆記包含兩份新測試的完整程式；logs/ 提供實際執行輸出。

以下 SHA-256 針對本次交付的設計與新測試：

| 檔案 | SHA-256 |
| --- | --- |
| rtl/fault_v_pkg.sv | `e167e90e84ca4de944393a8aa0da81f5ac6bd34ac617eac64e6a0a34c8737475` |
| rtl/control_fsm.sv | `4f890934ec57531b5687ee1abae0e83ceea1033d4dee5b20c8498bf0a610d4a8` |
| verify/tb_control_fsm.sv | `872c9d6fbc6c90c5ff7fb96054449a27eb46417810ab9bbc3d92e3020171fb3b` |
| verify/tb_control_path.sv | `d26b8e0d9a1b1a2091edfa2e02d61c5a0f4ad40c302f24fec5731bd8c3407a77` |
