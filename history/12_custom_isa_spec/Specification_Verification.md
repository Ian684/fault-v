# 自訂指令規格模型驗證紀錄

執行日期：2026-10-13（Asia/Taipei）。命令：`python verify_spec.py`，Python 程序退出碼 0。證據：`spec_verification.log`。

| 驗證 | 數量／結果 |
| --- | --- |
| 固定 directed 邊界 | 14 筆，包括 DOT4 最大／最小、MUL16 忽略高位、飽和、負數右移及 shift 高位忽略 |
| 獨立隨機 oracle | 每條 4096 筆，共 16384 筆；固定種子 0xFA017 |
| 編碼／解碼 | 四指令 × 32 rd × 32 rs1 × 32 rs2 = 131072 組 |
| 合法／非法編碼 | 128 funct7 × 8 funct3 與 128 opcode，共 1152 組 |
| 暫存器語意 | 28 組，包含 rd=rs1、rd=rs2、兩來源相同、x0 來源與目的 |
| 工作負載 | 129 項核對，DOT64、FIR8＋QNT8、FIR16、SATADD64 |
| 總計 | **148779 checks passed** |

```text
ALL 148779 SPECIFICATION CHECKS PASSED
```

reference.py 以位元擷取與算術右移建模；隨機 oracle 獨立使用 byte 解讀、整數除法與界限判斷。工作負載的 shift/add 基準模型、custom 模型與直接數學運算互相比對。

DOT64 預期 60256。完整輸入與 FIR／量化／飽和輸出列在 benchmark_vectors.json；cycle 與 speedup 為 null，沒有填入推測效能。

檢查現有 network_bridge RTL：Register File 為兩讀一寫，CPU state enum 為 4-bit、15 種狀態，WB 選擇為 2-bit／3 種来源。規格對應沿用兩讀埠、新增 CustomResult／第四種 WB，以及增加三種狀態後擴為至少 5-bit。

本交付沒有修改既有 CPU RTL、沒有建立 custom unit RTL、沒有執行硬體模擬／綜合／FPGA 下載，沒有聲稱硬體加速完成。Assembly .insn 為依官方文件提供的寫法，本次未以 GNU assembler 編譯。隨機測試不是形式證明，也不是窮舉全部 64-bit 輸入組合。

規格版本：XFaultVDSP v1.0。名稱是專案自訂，不是 RISC-V ratified extension。編碼依 custom-0 空間，四種 funct3 / funct7 規則以本專案文件為準。
