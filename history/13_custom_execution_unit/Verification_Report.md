# DSP／AI CPU 驗證紀錄

執行日期：2026-10-13（Asia/Taipei）。工具：Vivado / XSim 2022.2。

## 實際 RTL 模擬

| 項目 | 結果 | 證據 |
| --- | --- | --- |
| custom_exec 結果比對 | 16398 個 fixed／random 向量與 11 次 reset 後重跑，共 16409 個完整結果正確 | logs/tb_custom_exec.log |
| 單元 reset 取消 | 11 次；接受 16420 筆 = 完成 16409 筆 + 取消 11 筆 | logs/tb_custom_exec.log |
| 單元握手 | 鎖存輸入、忙碌不接受新請求、0～6 拍 response backpressure、取走一次、reset 無 stale response | verify/tb_custom_exec.sv 與成功紀錄 |
| CPU 自訂案例 | 1319 案例 × 2 種記憶體延遲，共 2638 次 | logs/tb_custom_cpu.log |
| 非法 custom 欄位 | 每模式 1020 個非法 funct7／funct3 組合全部 HALT_ILLEGAL；合法案例包含 x0、alias、相依與連續指令 | logs/tb_custom_cpu.log、verify/cpu.vec |
| CPU 提交 | PC 僅提交時前進；無提前寫回；retire word／rd／data、完整 RegFile 與 RAM 結果比對 | verify/tb_custom_cpu.sv 與成功紀錄 |
| CPU reset 階段 | 7 個 START／DOT4 WAIT／response／COMMIT 前位置；reset 後重跑只提交一次且 x5=70 | logs/tb_custom_reset.log |
| 工作負載程式 | 4 次正常執行，每次 127 個輸出逐項一致、270 次 custom 提交、8 UART bytes | logs/tb_custom_program.log |
| 工作負載失敗路徑 | 4 次 fault injection，兩延遲模式各早期／晚期；檢查編號 1 與 114、status=2、LED F、EBREAK | logs/tb_custom_program.log |
| 原 ISA／程式 | 1372 次回歸，兩模式各 40/40 指令名稱覆蓋 | logs/tb_verification_suite.log |
| 原 IO | 16 筆交易、2 個 serial bytes | logs/tb_fault_v_io.log |
| 原 IO fault | 8 案例通過 | logs/tb_io_faults.log |
| 原 stress | 4 次完整程式、4096 UART bytes、4 次 RAM／UART 執行中 reset | logs/tb_stress.log |
| 50 MHz FPGA wrapper | run 控制、BTN reset、三次完整 DSP 程式，共 24 UART bytes、debug=0x1205、LED=5 | logs/tb_payload.log |

單元向量隨機種子 0x1718；每指令 4096 個 random 輸入與 14 個 directed 邊界。CPU 另有每指令 64 個 random 來源、28 個 x0／alias、14 個 directed、1 個連續 custom 程式，以及非法函數編碼組合。

工作負載是 DOT64、FIR8＋QNT8、FIR16、SATADD64 與 14 個 directed 邊界。自我檢查程式 2469 words，仍在 4096-word IMEM 內。錯誤跳躍使用短 BEQ＋JAL，避免超過 B-type 範圍；生成器檢查所有 branch／JAL 位移。

重新產生 generate.py 後，custom_demo.mem、cpu.vec、unit.vec、demo_outputs.vec 的 SHA256 與已測試版本一致。

## FPGA 建置

| 項目 | 最終結果 | 證據 |
| --- | --- | --- |
| 建置 | CUSTOM FPGA BUILD PASSED；整合後 DSP count = 1 | logs/final_build.log |
| Clock 約束 | 50 MHz | logs/timing.rpt |
| Setup／Hold／Pulse width | WNS 7.756 ns、WHS 0.064 ns、WPWS 9.020 ns；全部指定約束符合 | logs/timing.rpt |
| DRC | 0 Error／Critical Warning；保留 4 個 Warning：DPIP-1×2、DPOP-1、DPOP-2 | logs/drc.rpt |
| Methodology | 0 violations | logs/methodology.rpt |
| Routing | 0 routing errors | logs/route.rpt |
| 資源 | 2760 LUT、2697 registers、8 BRAM tiles、1 DSP | logs/utilization.rpt |
| UART IP | 115200 baud 設定、50 MHz AXI clock | fault_v_custom.hwh |

初次合成把單一 product 表達式融合成 DOT4 的乘加 DSP 與 MUL16 的乘法 DSP，共 2 顆，故未採用該版交付。最終使用獨立 fault_v_mul16 階層防止複製，獨立候選合成與整體 routed design 都核對為 1 顆 DSP，且最終 RTL 全部重跑模擬。

PSU-1／PSU-2 negative DDR skew (-0.009／-0.033) 為沿用板上 PYNQ base preset 的保留 critical warnings；沒有修改或豁免這些 board parameters，也未執行 ps7_init。BD 41-702 的 50／50.0 傳播值提示保留。Synth 的未用位元／最佳化、BRAM output register 等提示不等於建置完全無 Warning。若工具產生 vectorless power activity 警告，不以其估計值宣稱實際功耗。

四個 DRC Warning 提示 DSP 的 A／B input、MREG、PREG 未使用內建 pipeline。這版以組合乘法配合外部暫存器達到 50 MHz 約束；保留這些效能／功耗最佳化提示，不改 severity、不宣稱 zero violations。封裝腳本只接受上述明列的四個 Warning，未知規則或其他 severity 會拒絕交付。

資源包含 PS 介接、AXI UART Lite、GPIO 與記憶體；不是單獨 CPU ASIC 面積。不同程式 ROM 內容與平台會影響資源，不能直接把與舊示範版的差值當成純指令擴充成本。

## 實板與效能範圍

2026-10-14 使用者接好 Z2 後，已透過 SSH / PYNQ 載入本版配對 bitstream／HWH，程序退出碼 0。

| 實板項目 | 結果／證據 |
| --- | --- |
| FCLK0 | ARM 讀到 50.0 MHz |
| UART | 三次各 8 bytes，完全符合 DSP OK + CR/LF，共 24 bytes |
| 接收錯誤 | parity／frame／overrun 累積旗標均為 0；無多餘 FIFO 字元 |
| CPU 結束 | 三次 program_status=1、halted=1、halt_cause=9 |
| 程式內容 | 每輪依自我檢查程式核對 127 項結果；包含四條指令及全部工作負載，非實板 retire counter 量測 |
| LED／BTN0 | 使用者確認：LD0／LD2 亮，LD1／LD3 滅；按住 BTN0 四燈熄滅，放開後 LD0／LD2 恢復。此為使用者觀察證據 |
| 證據 | logs/custom_fpga_uart.log、logs/board_verification.json |

部署位置：`/home/xilinx/jupyter_notebooks/fault_v_custom_20261014_194525`。實際執行的是 SSH / sudo Python；Notebook 是供使用者重跑的入口，本次未執行 Notebook 本身。

這項證據涵蓋本版自訂 CPU、內部 UART 收發、ARM AXI 讀取與 Ethernet 輸出，不是舊版測試結果。

單元 4／1 拍運算延遲不是完整 CPU cycle 或工作負載加速比。本次未建立與執行完整 RV32I 軟體 baseline，未進行 Week19 的公平效能比較；不宣稱四條指令均有加速。

測試為有限輸入與有限 reset 時刻，並非 formal proof。Wrapper RTL 模擬不包含 PS7／AXI UART Lite 實體運作、外部 Pmod pad／接線、ASIC 或製造測試。


## 交付檔案 SHA256

- fault_v_custom.bit：`8c905499d397415d7cce6825a7e8936bc67e7a59fe9576c7aa9c1b96ab0bdbf8`
- fault_v_custom.hwh：`b8aae20902ac1fe6044b2e89a143480c759db01ef6c93029770c8236df4d0d14`
- programs/custom_demo.mem：`6a69cd1e97767347e80d56596155fd063e8131cfb9923dd057cd3811f53338c9`
- rtl/custom_exec.sv：`053154dde5193de80c7bef9df9e17dc0c4016c88fbf317b78e34e7d45d83f9fb`
