from pathlib import Path
import json
root=Path(__file__).resolve().parent
p=json.loads((root/'program_spec.json').read_text(encoding='utf-8'))
intro='''# Fault-V：整數指令 CPU Datapath

## ① 模組用途與範圍

`fault_v_cpu` 把 Decoder、Immediate Generator、Register File、ALU、PC 與 Control FSM 接成實際硬體資料路徑。Testbench 只提供時脈、reset、指令記憶體回應與檢查結果；CPU 內部的指令、運算元、寫回及 PC 更新皆由 RTL 控制。

| 項目 | 規格 |
| --- | --- |
| 資料寬度 | 32-bit |
| 微架構 | 多周期、一次執行一條指令、FSM 控制 |
| 指令長度 | 固定 32-bit，順序位址加 4 |
| Register File | 32×32-bit，兩讀一寫，x0 固定為 0 |
| Reset | 高有效、同步 reset；PC 與內部暫存器清為 0 |
| 核心可執行範圍 | 21 種整數運算指令，以及 FENCE、ECALL、EBREAK 的既定行為 |
| 記憶體交易 | 指令請求／回應握手，一次最多一筆；允許等待 |
| 資料介面 | 保留接腳，尚未連接 Load／Store 資料路徑 |
| 錯誤處理 | 停止、保存原因與位址，直到 reset |
| 使用環境 | 裸機；沒有標準 trap／CSR／中斷 |

**Decoder 能辨識的指令比這個 top 能執行的指令多。這個 top 是 RV32I 整數運算子集，不能宣稱已完成完整 RV32I CPU。**

| 指令類別 | 指令 | 行為 |
| --- | --- | --- |
| R-type，10 種 | ADD、SUB、AND、OR、XOR、SLL、SRL、SRA、SLT、SLTU | A 與 B 運算，結果寫回 rd |
| I-type 運算，9 種 | ADDI、ANDI、ORI、XORI、SLTI、SLTIU、SLLI、SRLI、SRAI | A 與立即數運算，結果寫回 rd |
| U-type，2 種 | LUI、AUIPC | 立即數，或 InstrPC＋立即數，寫回 rd |
| FENCE | FENCE | 無資料存取及寫入緩衝的本子集，依序完成後繼續 |
| 停止指令 | ECALL、EBREAK | 分別以 HALT_ECALL／HALT_EBREAK 停止，PC 不前進 |
| 尚未接入 | Branch、JAL／JALR、Load／Store | 即使 Decoder 認得，也以 HALT_ILLEGAL 停止 |
| 不支援擴充 | MUL、CSR、壓縮指令等 | 非法指令停止 |

加減法保留低 32-bit，不因整數溢位停止。SLT／SLTI 採 signed 比較；SLTU／SLTIU 採 unsigned 比較，但 SLTIU 的立即數仍先做符號擴展。所有移位只使用第二運算元的低 5-bit。SRA／SRAI 複製符號位。

## ② Datapath 架構

```text
PC → 指令請求介面 → 指令回應資料 → IR → Decoder
 │                                  ├→ rs1／rs2／rd 編號
 └→ InstrPC（取指成功時保存 PC）      ├→ ALU 與 MUX 控制
                                    └→ imm_sel → imm_gen → imm

rs1／rs2 → Register File → A／B 暫存器

A／InstrPC／0 → ALU 左輸入 MUX ┐
B／imm       → ALU 右輸入 MUX ├→ ALU → ALUOut → Register File rd
                              ┘
InstrPC + 4 → PC next → PC（正常完成時更新）

Control FSM → 各暫存器 enable、記憶體握手、錯誤停止及 commit trace
```

| 保存位置 | 寬度 | 更新條件 | 用途 |
| --- | --- | --- | --- |
| PC | 32-bit | reset 或 pc_we | 下一次取指位址；執行與等待期間保持 |
| IR | 32-bit | ir_we | 取指成功的完整指令 |
| InstrPC | 32-bit | instr_pc_we，與 IR 同時 | 目前指令所在位址，供 AUIPC 與下一個 PC 計算 |
| A、B | 各 32-bit | ab_we | Decode 階段保存兩個讀取埠資料 |
| ALUOut | 32-bit | aluout_we | Execute 階段保存運算結果，供下一拍寫回 |
| Register File | 32×32-bit | reg_we，上升緣寫入 | 架構暫存器；rd＝0 的寫入忽略 |
| State／pending／錯誤資訊 | 依既有 controller 定義 | FSM 內部控制 | 保存狀態、交易及停止資訊 |

| 指令 | ALU A | ALU B | 寫回資料 |
| --- | --- | --- | --- |
| R-type | A | B | ALUOut |
| I-type 運算 | A | imm | ALUOut |
| LUI | 0 | U-type imm | ALUOut＝imm |
| AUIPC | InstrPC | U-type imm | ALUOut＝InstrPC＋imm |

`ALU_A_PC` 在這裡代表 **InstrPC**。同一條指令使用的 IR、InstrPC、A、B 在運算及寫回期间保持；不能拿已前進的 PC 計算 AUIPC。

## ③ 狀態與更新時機

| 狀態 | 動作 | 上升緣更新 |
| --- | --- | --- |
| FETCH：尚未接受請求 | 保持 imem_req_valid 與位址，等待 req_ready | 接受請求後保存 pending |
| FETCH：請求已接受 | 不重複送請求，等待有效回應 | 成功回應時更新 IR、InstrPC，進入 DECODE |
| DECODE | 解碼，檢查非法指令或 top 未接入的指令類別 | 一般整數指令保存 A／B，進入 ALU_EXEC |
| ALU_EXEC | MUX 選輸入，ALU 做對應運算 | ALUOut 保存結果，進入 ALU_WB |
| ALU_WB | 開啟 reg_we、pc_we、instr_done | 寫回 rd，PC＝InstrPC＋4，回到 FETCH |
| FENCE_COMMIT | 不寫 rd，開啟 pc_we、instr_done | PC＝InstrPC＋4，回到 FETCH |
| HALTED | 不發起請求、不寫回、不更新 PC | 保存停止狀態直到 reset |

順序相依指令不需要 forwarding：前一條指令完成寫回後，才取下一條指令。若 rd 與 rs1 相同，A 在 Decode 已保存舊值，之後寫回新值，不會破壞該次運算。

本測試的取指記憶體會先接受請求，再於後續時脈回應；不能把同一個 edge 的首次 request acceptance 當成 response acceptance。回應必須保持到 rsp_valid 且 rsp_ready 的上升緣。

## ④ Top 模組介面

| 訊號 | 方向 | 寬度 | 定義 |
| --- | --- | --- | --- |
| clk／rst | 輸入 | 各 1 | 單一 clock、高有效同步 reset |
| imem_req_valid／imem_req_ready | 輸出／輸入 | 各 1 | 取指請求握手 |
| imem_req_addr | 輸出 | 32 | Byte address；正常取指對齊 4 bytes |
| imem_rsp_valid／imem_rsp_ready | 輸入／輸出 | 各 1 | 取指回應握手 |
| imem_rsp_data／imem_rsp_err | 輸入 | 32／1 | 指令資料／存取失敗 |
| dmem_req_valid／dmem_req_ready | 輸出／輸入 | 各 1 | 保留資料請求介面；本 top 不發交易 |
| dmem_req_write／dmem_req_addr | 輸出 | 1／32 | 資料讀寫方向／位址 |
| dmem_req_wdata／dmem_req_wstrb | 輸出 | 32／4 | 本版固定 0，尚未接 Store 格式化 |
| dmem_rsp_valid／dmem_rsp_err／dmem_rsp_data | 輸入 | 1／1／32 | 保留資料回應介面 |
| dmem_rsp_ready | 輸出 | 1 | 本子集保持 0 |
| halted／halt_cause | 輸出 | 1／4 | 停止狀態與原因 |
| fault_pc／fault_addr | 輸出 | 各 32 | 錯誤上下文；依原因定義 |
| pc／state | 輸出 | 32／4 | 除錯觀察訊號 |

### Commit 觀察介面

| 訊號 | 寬度 | 定義 |
| --- | --- | --- |
| retire_valid | 1 | 該上升緣正常完成一條指令 |
| retire_pc／retire_instruction | 各 32 | 完成指令的位址／機器碼 |
| retire_rd_we | 1 | 該指令真的寫入 x1～x31；寫 x0 或 FENCE 為 0 |
| retire_rd_addr／retire_rd_data | 5／32 | 寫入編號／值；未寫入時輸出 0 |

這些是組合輸出，應在完成指令的 **clock 上升緣、非阻塞更新之前**取樣。若等待 PC／State 更新後才讀，訊號可能已變成下一個狀態。這是專案自訂 trace，並非完整 RVFI。停止或錯誤的指令不產生正常 retire_valid。

## ⑤ 完整 CPU Top RTL

既有 `fault_v_pkg.sv`、`control_fsm.sv`、`decoder.sv`、`alu.sv`、`imm_gen.sv`、`regfile.sv`、`pc_reg.sv` 應與下面的 top 一起使用。檔案包包含相同介面版本，不要同時匯入重複的 package 或同名 module。

'''
note=intro+'```systemverilog\n'+(root/'rtl/fault_v_cpu.sv').read_text()+'```\n\n'
note+='''## ⑥ 程式與預期结果

下面是一段有前後資料相依的連續程式，不是逐條 reset 的單元測試。Byte address 從 0 開始，每條加 4。表中的結果是架構寫回值；x0／FENCE 不寫入，trace 資料為 0。

| PC | 指令 | 機器碼 | 寫回 | 預期值 |
| --- | --- | --- | --- | --- |
'''
for i,(asm,word,rd,value) in enumerate(p):
    note+=f'| `0x{i*4:08X}` | `{asm}` | `{word:08X}` | '+(f'x{rd}' if rd else '不寫入')+f' | `{value:08X}` |\n'
note+='| `0x00000094` | `ebreak` | `00100073` | 停止 | cause＝9、fault_pc＝0x94、fault_addr＝0 |\n\n'
note+='''其中 `lui x31,0x80000` 先得到 `0x80000000`，再加 -1 得到 `0x7FFFFFFF`，最後加 1 得到 `0x80000000`，驗證加法只保留低 32-bit。AUIPC 位於 `0x68`，所以結果是 `0x68＋0x1000＝0x1068`。

## ⑦ 驗證設計與驗收條件

| 情境 | 驗證重點 | 預期結果 |
| --- | --- | --- |
| 相依整數程式，三組取指延遲 | 全部 21 種整數運算、FENCE、x0、同址讀寫、取指等待 | 各 37 次正常 commit、38 次取指，EBREAK 停於 0x94 |
| Load／Branch／Jump | top 範圍限制確實阻止未接入路徑 | 各在 PC＝4 以非法指令原因停止，不發資料交易 |
| MUL／非法 shift 編碼 | 未支援擴充與編碼檢查 | PC＝4、HALT_ILLEGAL |
| ECALL | 與 EBREAK 區分 | PC＝4、HALT_ECALL |
| 第二次取指失敗 | 保留已完成指令的寫回，保存失敗位址 | x1＝5，PC／fault_pc／fault_addr＝4、HALT_FETCH_ACCESS |
| 請求已接受時 reset，再重跑 | 核心與記憶體共同 reset，清掉舊回應 | 從 PC＝0 重新執行完整程式 |

每次正常 commit 都檢查指令、InstrPC、目的暫存器、寫入值；等待期間檢查 PC 保持與請求位址稳定。停止後比較全部 32 個實際暫存器與預期模型，並再等待四拍確認不繼續執行。程式測試涵蓋上述案例，沒有把有限案例當成所有輸入的完整證明。

測試記憶體只有 64 words，用來模擬本程式，**不是最終 16 KiB 記憶體實作**。reset 測試要求核心與記憶體一起清掉 pending／舊回應；若整合獨立外部記憶體，必須另訂 reset 期間的交易處理。

### Testbench：tb_fault_v_cpu.sv

'''
note+='```systemverilog\n'+(root/'verify/tb_fault_v_cpu.sv').read_text()+'```\n\n'
note+='### 預期值表：program_init.svh\n\n此檔案由 testbench 的 `include` 引入，與 testbench 放在相同 `verify` 資料夾。預期運算值為固定常數，不是讀取 DUT 結果產生。\n\n```systemverilog\n'+(root/'verify/program_init.svh').read_text()+'```\n\n'
note+='''## ⑧ Vivado 模擬方式

1. 解壓縮檔案包，資料夾放在一般本機路徑。
2. Design Sources 加入 `rtl` 內的八個 `.sv`；`fault_v_pkg.sv` 編譯順序應在使用它的模組之前。
3. Simulation Sources 加入 `verify/tb_fault_v_cpu.sv` 及 `verify/program_init.svh`。如果 include 找不到，將 `verify` 的完整路徑加入 Simulation 的 Include Directories。
4. 把 **Simulation Top** 設成 `tb_fault_v_cpu`；若之後綜合，Design Top 才是 `fault_v_cpu`。
5. 執行 Behavioral Simulation，Tcl Console 輸入 `run all`。只跑 1000 ns 不足以跑完全部案例。
6. 檢查下方最後一行與 `$finish`；不能只看前幾筆 PASS。

`alu_program.mem` 和 `.S` 是同一段程式的參考檔；目前 testbench 透過 `program_init.svh` 載入，不需要把 `.mem` 當成 RTL 或手動新增 `$readmemh`。

預期關鍵輸出：

```text
PASS 1: dependent integer program committed=37 requests=38 pc=00000094 cause=9
PASS 2: dependent integer program committed=37 requests=38 pc=00000094 cause=9
PASS 3: dependent integer program committed=37 requests=38 pc=00000094 cause=9
PASS 4: load not yet supported committed=1 requests=2 pc=00000004 cause=1
PASS 5: branch not yet supported committed=1 requests=2 pc=00000004 cause=1
PASS 6: jump not yet supported committed=1 requests=2 pc=00000004 cause=1
PASS 7: MUL not supported committed=1 requests=2 pc=00000004 cause=1
PASS 8: illegal shift encoding committed=1 requests=2 pc=00000004 cause=1
PASS 9: ECALL stops with own cause committed=1 requests=2 pc=00000004 cause=8
PASS 10: fetch failure preserves prior write committed=1 requests=2 pc=00000004 cause=3
PASS 11: reset during accepted fetch then restart committed=37 requests=38 pc=00000094 cause=9
ALL 11 INTEGER CPU PROGRAM SCENARIOS PASSED
```

也可用 PowerShell 執行檔案包內 `run_xsim.ps1`。功能模擬不需要上板，不需要 FPGA pin constraints；模擬的 10 ns clock 只定義測試步進，並不代表 FPGA／ASIC 已達成 100 MHz 時序。

## ⑨ 檔案用途與後續整合界線

| 路徑 | 用途 |
| --- | --- |
| rtl/fault_v_cpu.sv | 真正 CPU top 及內部資料路徑 |
| rtl 其餘七個 .sv | 共用型別與既有功能模組 |
| verify/tb_fault_v_cpu.sv | 記憶體模擬、測試情境、commit 檢查 |
| verify/program_init.svh | 機器碼與固定預期值 |
| verify/alu_program.S／.mem | 組合語言與對應機器碼 |
| run_xsim.ps1 | 批次編譯與模擬 |
| logs/integer_cpu_results.log | 獨立模擬結果證據 |

接入 Branch／Jump 時需加入比較器、BranchTaken、目標對齊檢查及 link 寫回來源；接入 Load／Store 時需加入 MDR、byte enable、Store 對齊及 Load 擷取／擴展邏輯。**不能只移除 core_illegal 的限制就宣稱支援這些指令。**

綜合、FPGA 時序／實板驗證與 ASIC 實作是另外的驗收工作，應保留各自的報告。
'''
(root/'Integer_CPU_Datapath_Notion.md').write_text(note,encoding='utf-8')
