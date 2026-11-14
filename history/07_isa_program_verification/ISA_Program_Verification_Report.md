# Fault-V：指令與程式驗證紀錄

- 日期：2026-10-07。
- 工具：Vivado 2022.2 XSim behavioral simulation。
- DUT：`fault_v_soc`；Simulation Top：`tb_verification_suite`。
- RTL 與前一整合版相同，沒有修改 CPU 或記憶體模組。
- 編譯、elaboration 與交付用 `run_xsim.ps1` 實際執行成功。
- 結果：`ALL 1372 ISA AND PROGRAM RUNS PASSED`。
- 正常 `$finish`：618327 ns，沒有 Fatal。

| 類別 | 獨立案例 | 實際執行 |
| --- | --- | --- |
| 支援指令 focused cases | 664 | 1328，兩種延遲 |
| 非法／未支援編碼 | 10 | 20，兩種延遲 |
| 程式級案例 | 6 | 24，兩種延遲，各執行與 reset 重跑 |
| 合計 | 680 | 1372 |

兩個模式的 IMEM／DMEM 回應延遲為 1／1 和 4／7 clocks；各執行 686 次，均觀察到指令名稱覆蓋 40／40：

```text
COVERAGE mode=0 names=40/40 bitmap=ffffffffff runs=686
COVERAGE mode=1 names=40/40 bitmap=ffffffffff runs=686
```

target instruction 的 PC 必須實際 commit，或在指定 PC 發生預期的合法指令錯誤／停止事件，才計入覆蓋。ECALL／EBREAK 不以正常 retire 計數。這是名稱與 focused case 覆蓋，不是 RTL code coverage 或正式 ISA compliance。

| 程式 | 驗收結果 |
| --- | --- |
| fibonacci_12 | RAM 中 F0～F11 正確，最後值 89 |
| loop_sum_100 | x3 與 RAM[0]＝5050 |
| gcd_48_18 | x10 與 RAM[0]＝6 |
| nested_call_aligned_stack | 返回結果 42，sp 恢復 0x10004000，16-byte frame 保存 ra |
| memory_copy_64_checksum | 64 words 複製一致，checksum＝2016 |
| subword_signed_memory | signed／unsigned 擴展正確，最終 word＝0x123400EF |

六個程式在兩種延遲下，首次與保留 RAM 後重跑皆通過，status＝1，依預期 EBREAK 停止。

每次資料交易比對位址、方向、wdata／mask、完整回應 word／error；每次 commit 比對 InstrPC、機器碼、rd enable／地址／值及下一個 PC。每個案例停止後比較全部 32 個暫存器和完整 16 KiB 資料 RAM，並確認 halt context、status、交易數及停止後不繼續執行。

首次執行在 Fibonacci 重跑抓到預期模型問題：RAM 保留內容後，Store 的 response 是「寫入前舊 word」，測試卻沿用首次清 RAM 時的預期 response。修正模型，使重跑从第一次最後 RAM 開始、status 清為 0；最終 trace／RAM 必須一致，raw response 可依舊內容改變。修正後重新編譯並執行完整套件通過，沒有修改 CPU／系統 RTL。

新案例在 reset 下由 testbench 裝入指令 RAM 並準備資料 RAM，是測試 fixture；執行期間不修改核心寄存器，不替 RTL 記憶體回應。六個程式的重跑則不清 RAM、不重新裝入影像。這不代表已加入硬體 runtime loader。

R-type 額外樣本採固定 seed 20261007。預期模型以指令數學語意和 byte array 運作，與 RTL 週期安排分離。程式有固定結果斷言；所有 `.S`／`.mem` 由專案編碼器產生，沒有使用 GNU／LLVM assembler 或 C toolchain。

原始證據：`logs/verification_results.log`；逐指令對照：`coverage.json`；完整案例：`suite.json`、`verify/suite.vec`。重現方式：`run_xsim.ps1`。RTL SHA-256 存於 `rtl_sha256.json`。

本次完成規格中的逐指令與程式級功能驗收，未驗收 FPGA synthesis／implementation／時序／實板、UART／GPIO 或 ASIC sign-off；不把有限案例或 40／40 指令名稱覆蓋視為全輸入證明。
