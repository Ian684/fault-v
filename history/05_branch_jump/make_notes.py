from pathlib import Path
import json,re
root=Path(__file__).resolve().parent
cases=json.loads((root/'cases.json').read_text())
note='''# Fault-V：Branch 與 Jump CPU Datapath

## ① 指令語意與支援範圍

這個 CPU top 在既有整數運算資料路徑上加入條件分支及跳躍，可以執行迴圈與函式呼叫／返回。保持 32-bit、多周期、FSM、單指令依序執行；每條指令正常完成後才更新 PC。

| 項目 | 規格 |
| --- | --- |
| 模組名稱 | `fault_v_cpu` |
| 既有整數運算 | 10 種 R-type、9 種 I-type、LUI、AUIPC |
| Branch | BEQ、BNE、BLT、BGE、BLTU、BGEU |
| Jump | JAL、JALR |
| 其他既定行為 | FENCE 依序完成；ECALL／EBREAK 停止並區分原因 |
| 指令對齊 | 4-byte，未加入 C 壓縮指令 |
| 記憶體 | 指令請求／回應握手，一次最多一筆 |
| 尚未接入 | Load／Store；在 top 以非法指令停止 |
| 執行環境 | 裸機，自訂 halt／debug；沒有標準 machine-mode trap／CSR／中斷 |

這仍是 RV32I 的子集。Decoder 雖能辨識 Load／Store，但資料讀寫路徑尚未接入，不能只靠解碼成功就宣稱完整支援 RV32I。

| 指令 | 比較條件／目標 | 正常完成時寫回 | 正常完成時 PC |
| --- | --- | --- | --- |
| BEQ | A＝B | 無 | 成立：InstrPC＋imm；否則 InstrPC＋4 |
| BNE | A≠B | 無 | 同上 |
| BLT | signed A＜signed B | 無 | 同上 |
| BGE | signed A≥signed B | 無 | 同上 |
| BLTU | unsigned A＜unsigned B | 無 | 同上 |
| BGEU | unsigned A≥unsigned B | 無 | 同上 |
| JAL | InstrPC＋imm | rd＝InstrPC＋4；rd＝x0 時忽略寫入 | 目標 |
| JALR | (A＋imm) 清除 bit 0 | rd＝InstrPC＋4；rd＝x0 時忽略寫入 | 清除 bit 0 後的目標 |

**分支／JAL 的立即數是相對於目前指令 InstrPC 的 byte offset。imm_gen 已補上 B／J 的最低位 0，不可再左移。JALR 使用符號擴展的 I-type 立即數，不能把它當成 B／J 格式。**

### signed 與 unsigned 比較

| A | B | signed A＜B | unsigned A＜B |
| --- | --- | --- | --- |
| 0xFFFFFFFF | 0x00000001 | 真，-1＜1 | 假，4294967295＞1 |
| 0x80000000 | 0x7FFFFFFF | 真，最小 signed 值＜最大 signed 值 | 假 |
| 0x00000007 | 0x00000007 | 假 | 假 |

BGE／BGEU 包含相等。不要用減法結果的最高位直接代替 signed 比較，因為減法可能溢位；比較器明確使用 `$signed`。

## ② 新增的 Datapath

```text
IR → Decoder → branch_op、alu_src_a／b、wb_sel、instr_class
 │
 └→ imm_gen → B／J／I 格式立即數

Register File → A、B 暫存器 → Branch Comparator → branch_condition
                                                    │
                                           branch_taken_we
                                                    ▼
                                               BranchTaken
                                                    │
                                                    ▼
                                               Control FSM

InstrPC／A → ALU 左 MUX ┐
imm        → ALU 右 MUX ├→ ALU → JALR bit 0 清除 → ALUOut
                       ┘                         │
                                                 ├→ 目標對齊檢查
                                                 └→ PC 目標來源

ALUOut／InstrPC＋4 → Writeback MUX → Register File rd
InstrPC＋4／ALUOut → PC MUX → PC（正常 commit 時更新）
```

| 元件／訊號 | 功能 | 更新或使用時機 |
| --- | --- | --- |
| branch_compare | 比較 A／B，支援六種條件 | 組合邏輯，沒有 clock／reset |
| branch_condition | 比較器當下結果 | 在 BR_EXEC 供保存 |
| branch_taken | 1-bit 暫存器，保存分支成立結果 | branch_taken_we 時更新；reset 清 0 |
| ALUOut | 保存 Branch／JAL／JALR 最終目標 | Execute 結束時更新 |
| JALR bit 0 清除 | 將加法結果最低位設為 0 | 保存 ALUOut 前處理 |
| Writeback MUX | WB_PC4 選 InstrPC＋4，其餘已支援指令選 ALUOut | 寫回及 commit trace 使用同一個 wb_data |
| PC MUX | PC_SEQ 選 InstrPC＋4，PC_TARGET 選 ALUOut | pc_we 時保存到 PC |

| 指令類別 | ALU A | ALU B | ALU 動作 |
| --- | --- | --- | --- |
| Branch | InstrPC | B-type imm | ADD，與比較器同時工作 |
| JAL | InstrPC | J-type imm | ADD |
| JALR | A 暫存器 | I-type imm | ADD，再清除 bit 0 |

當 JALR 的 rd＝rs1，A 在 Decode 已保存跳躍前的 rs1，所以先使用舊值計算目標，再把返回位址寫入同一個暫存器。`jalr x5,0(x5)` 不能先寫 x5 再用新 x5 計算目標。

## ③ 狀態與控制訊號

取指成功後保存 IR／InstrPC；Decoder 的控制輸出在該指令完成前保持，A／B 在 Decode 保存。取指等待期間 PC 保持。

| 狀態 | 動作 | 主要 enable | 下一狀態 |
| --- | --- | --- | --- |
| DECODE，Branch | 保存 A／B | ab_we | BR_EXEC |
| BR_EXEC | ALU 計算目標，比較器判斷條件 | aluout_we、branch_taken_we | BR_COMMIT |
| BR_COMMIT，不成立 | 不寫 rd，正常完成 | pc_we、instr_done；PC_SEQ | FETCH |
| BR_COMMIT，成立且對齊 | 不寫 rd，正常完成 | pc_we、instr_done；PC_TARGET | FETCH |
| BR_COMMIT，成立但未對齊 | 記錄錯誤，不更新 PC／rd | halt event | HALTED |
| DECODE，JAL／JALR | 保存運算元 | ab_we | JUMP_EXEC |
| JUMP_EXEC | 計算目標；JALR 清除 bit 0 | aluout_we | JUMP_COMMIT |
| JUMP_COMMIT，對齊 | 寫返回位址並跳躍 | reg_we、pc_we、instr_done；PC_TARGET | FETCH |
| JUMP_COMMIT，未對齊 | 記錄錯誤，不寫返回位址 | halt event | HALTED |

PC 更新和 JAL／JALR 寫回發生在同一個正常完成上升緣。BR_EXEC、JUMP_EXEC 只保存中間結果，不提前更新 PC。

## ④ 對齊、錯誤与返回位址

| 情況 | 行為 |
| --- | --- |
| Branch 不成立，計算目標未對齊 | 不跳躍，不因該目標報錯；PC＝InstrPC＋4 |
| Branch 成立，目標低 2-bit 非 00 | HALT_INSTR_ALIGN；fault_pc＝分支指令位址，fault_addr＝目標 |
| JAL 目標未對齊 | HALT_INSTR_ALIGN，PC 保持，rd 不寫入 |
| JALR 原始目標奇數 | 先清 bit 0，再檢查 4-byte 對齊 |
| JALR 清 bit 0 後 bit 1 仍為 1 | HALT_INSTR_ALIGN，PC 保持，rd 不寫入 |
| 對齊目標不在測試記憶體 | 跳躍正常 commit；下一次取指收到錯誤，HALT_FETCH_ACCESS |
| 目標取指失敗 | fault_pc／fault_addr＝取指目標；此前已完成的 link 寫回保留 |
| reset | 同步清核心暫存器及狀態；測試記憶體一起取消 pending／舊回應 |

例如 JALR 的 A＝0x13、imm＝0，清 bit 0 得到 0x12，仍未對齊；A＝0x11 則變成 0x10，可跳躍。核心不在 Execute 預先判斷記憶體容量，可存取範圍由外部記憶體的回應決定。

本設計遇錯誤會停止，沒有標準 trap handler。正常跳躍與下一條指令取指失敗是兩個不同事件，不能因下一次取指失敗而回滾已完成的跳躍寫回。

## ⑤ Branch Comparator：完整 RTL

| 接腳 | 方向 | 型別／寬度 | 說明 |
| --- | --- | --- | --- |
| a、b | 輸入 | logic [31:0] | 已保存的 rs1／rs2 資料 |
| branch_op | 輸入 | fault_v_pkg::branch_op_t，3-bit | Decoder 指定的比較條件 |
| taken | 輸出 | logic，1-bit | 條件成立；BR_NONE／未使用編碼預設 0 |

'''
note+='```systemverilog\n'+(root/'rtl/branch_compare.sv').read_text()+'```\n\n'
note+='''## ⑥ CPU Top：完整 RTL

Top 外部記憶體／debug／commit 接腳沿用整數 CPU 定義。`retire_valid` 與資料在完成指令的 clock 上升緣、非阻塞更新前取樣；是專案自訂 trace，不是完整 RVFI。Branch 正常完成會 retire，但 retire_rd_we＝0；JAL／JALR 寫 x0 時同樣為 0。

這份 top 使用檔案包中其餘八個 RTL 檔案。`fault_v_pkg.sv` 先編譯，`fault_v_cpu.sv` 只保留一份。資料介面的 wdata／wstrb 仍為 0，本範圍不發資料交易。

'''
note+='```systemverilog\n'+(root/'rtl/fault_v_cpu.sv').read_text()+'```\n\n'
note+='''## ⑦ 迴圈與函式呼叫：程式、位址與預期值

```asm
'''+(root/'verify/loop_call.S').read_text()+'''```

| PC | 指令 | 機器碼 | 作用 |
| --- | --- | --- | --- |
'''
loop=cases[37]
asm=['addi x1,x0,5','addi x2,x0,0','addi x3,x0,0','addi x2,x2,1','add x3,x3,x2','blt x2,x1,loop','jal x1,function','jal x0,done','addi x3,x3,10','jalr x0,0(x1)','ebreak']
effects=['次數上限＝5','計數器＝0','總和＝0','計數器＋1','總和＋計數器','小於 5 時跳回 0x0C','x1＝0x1C，跳至 0x20','不寫 x0，跳至 0x28','總和＋10','跳回 x1＝0x1C','停止']
for k,(a,w,e) in enumerate(zip(asm,loop['words'],effects)):note+=f'| `0x{k*4:02X}` | `{a}` | `{w:08X}` | {e} |\n'
note+='''
| 預期項目 | 值 |
| --- | --- |
| 迴圈五輪的 x3 | 1、3、6、10、15 |
| 函式執行後 x3 | 25＝0x00000019 |
| 最終 x2 | 5 |
| 最終 x1 | 0x0000001C |
| 正常 commit 數 | 22；包含五次 Branch、呼叫、返回及跳過函式的 JAL |
| 取指數 | 23，包含最後 EBREAK |
| 停止資訊 | PC／fault_pc＝0x28，cause＝HALT_EBREAK＝9，fault_addr＝0 |

### 巢狀呼叫

```asm
'''+(root/'verify/nested_call.S').read_text()+'''```

外層函式用 x5 保存呼叫它的返回位址 0x04，內層呼叫把 x1 更新為 0x10。內層返回至 0x10，外層再用 x5 返回至 0x04。預期最終 x10＝5、x5＝4、x1＝0x10，8 次正常 commit，EBREAK 位於 0x20。

這是沒有記憶體的測試範例，直接用另一個 register 保存返回位址；一般函式 ABI 的 stack 保存／還原要等 Load／Store 接入後再驗證。

## ⑧ Testbench 與預期模型

| 檢查項目 | 驗收條件 |
| --- | --- |
| 六種 Branch | 成立與不成立皆與預期路徑一致，包含負數、相等及 signed 極值 |
| 分支目標 | 正向、反向及位移邊界，依 InstrPC 計算 |
| JAL | 正向／負向跳躍、x0、link 與對齊行為正確 |
| JALR | 正／負立即數、立即數邊界、bit 0 清除、rd＝rs1、rd＝x0 正確 |
| Commit | 每次 InstrPC、機器碼、目的暫存器、寫回值與下一個 PC 符合預期 |
| 未完成指令 | PC 保持，請求在 backpressure 下保持位址及 valid |
| 錯誤 | 未對齊指令不 commit、不寫 link；目標取指失敗保存已寫 link |
| Reset | Branch／Jump commit 前 reset，再由起點重跑完整程式 |
| 回歸 | 整数程式、非法指令、ECALL 與取指失敗行为正確 |
| 最終狀態 | 全部 32 個實際暫存器符合獨立預期值，停止後保持不執行 |

`build_cases.py` 使用軟體的指令語意模型，由指令運算元和 label 計算预期 trace 與最終暫存器，**不讀 DUT 訊號或複製 FSM 的 cycle 動作**。編碼器另產生機器碼送到硬體；原整數程式維持既有固定常數預期值。這個模型只涵蓋測試使用的指令，不是完整 RISC-V simulator，也不是正式 ISA compliance 認證。

`cases_init.svh` 包含全部測試指令與預期表；`cases.json` 可用來查閱完整程式、逐次 trace 與最終暫存器。testbench 不會用 trace 寫入或修改 DUT 的暫存器，只在停止時讀取它們驗證。

### 完整 testbench

'''
note+='```systemverilog\n'+(root/'verify/tb_branch_cpu.sv').read_text()+'```\n\n'
note+='''### 所有程式的預期結果

每個程式分別以基本延遲和可變等待執行一次。下表的編號是 `load_case` 使用的 case_id。cause：1＝非法指令，2＝指令目標未對齊，3＝取指失敗，8＝ECALL，9＝EBREAK。

| case_id | 程式 | 正常 commit | 停止 PC | cause | fault_addr |
| --- | --- | --- | --- | --- | --- |
'''
for idx,c in enumerate(cases):
    cause,pc,addr=c['stop'];note+=f'| {idx} | {c["name"]} | {len(c["trace"])} | `{pc:08X}` | {cause} | `{addr:08X}` |\n'
note+='''
另有兩次在 BR_COMMIT／JUMP_COMMIT 前 reset，再重跑迴圈程式的情境。reset 前取消的指令不算進重啟後的 commit 次數。

預期最後输出：

```text
PASS 133: reset before control-flow commit then restart committed=22 requests=23 pc=00000028 cause=9
PASS 134: reset before control-flow commit then restart committed=22 requests=23 pc=00000028 cause=9
ALL 134 BRANCH CPU SCENARIOS PASSED
```

測試記憶體有 64 words，支援單筆取指交易，不是最終 16 KiB 的記憶體實作。大位移跳躍落在這個範圍外，模型故意回應存取失敗；這可以驗證跳躍已完成後的取指錯誤。模型沒有把「超出範圍」當成 CPU 對齊錯誤。

## ⑨ Vivado 使用方式

1. 解壓縮檔案包到一般本機資料夾。
2. Design Sources 加入 `rtl` 內九個 `.sv`。使用本包完整版本，避免同時加入舊 top、重複 package 或同名 module。
3. Simulation Sources 加入 `verify/tb_branch_cpu.sv` 與 `verify/cases_init.svh`。若找不到 include，將 `verify` 完整路徑加入 Simulation Include Directories。
4. Simulation Top 設成 **tb_branch_cpu**；Design Top 則是 **fault_v_cpu**。
5. 執行 Behavioral Simulation，Tcl Console 輸入 **run all**。1000 ns 不足以跑完全部情境。
6. 確認最后的 `ALL 134 BRANCH CPU SCENARIOS PASSED` 與正常 `$finish`，沒有 Fatal。

不需要先刪除 ALU、imm_gen 或 Register File；這些都是 top 的必要模組。舊 testbench 可留著，但本次要選對 Simulation Top。`.mem` 只是參考程式檔，本次 testbench 使用 `.svh` 初始化，不額外執行 `$readmemh`。

也可用 PowerShell 執行 `run_xsim.ps1`；預設 Vivado 2022.2 路徑，可用 `-VivadoBin` 指定其他安裝路徑。Python 只在重新產生测试資料時需要，直接執行既有 XSim 測試不需要 Python。

| 檔案 | 用途 |
| --- | --- |
| rtl/fault_v_cpu.sv | 加入 Branch／Jump 的 CPU top |
| rtl/branch_compare.sv | 組合比較器 |
| rtl 其他七檔 | package、FSM、Decoder、ALU、imm_gen、RegFile、PC |
| verify/tb_branch_cpu.sv | 取指模型、測試驅動與檢查 |
| verify/cases_init.svh | 完整機器碼／預期結果表 |
| verify/loop_call.S／nested_call.S | 可閱讀的範例程式 |
| verify/program_37.mem／program_38.mem | 迴圈／巢狀呼叫的逐行機器碼 |
| cases.json／build_cases.py | 預期結果與可重產生的指令語意模型 |
| reference_inputs | 重產生整數回歸資料所需的固定來源；不是本次 Simulation Sources |
| run_xsim.ps1 | 編譯、elaboration、模擬及 PASS 檢查 |
| logs/branch_cpu_results.log | 獨立模擬紀錄 |

模擬的 10 ns clock 是測試用時間步進，不代表已達成 FPGA／ASIC 100 MHz 時序。此處驗收功能行为；綜合、時序及實板驗證需要各自的證據。
'''
for a,b in [('期间','期間'),('稳定','穩定'),('结果','結果'),('整数','整數'),('输出','輸出'),('最后','最後'),('预期','預期'),('行为','行為'),('测试','測試'),('与','與')]:note=note.replace(a,b)
(root/'Branch_Jump_CPU_Notion.md').write_text(note,encoding='utf-8')
