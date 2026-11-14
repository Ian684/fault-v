from pathlib import Path
import json
root=Path(__file__).resolve().parent
cases=json.loads((root/'cases.json').read_text())
note='''# Fault-V：Load／Store 與資料記憶體介面

## ① 模組用途與整合範圍

這份 `fault_v_cpu` 在既有整數運算、Branch、JAL／JALR 上加入八種 Load／Store。CPU 能從資料記憶體讀取、運算，再把結果存回記憶體。

| 項目 | 規格 |
| --- | --- |
| 核心 | 32-bit，多周期，FSM 控制，一次一條指令 |
| Load | LB、LBU、LH、LHU、LW |
| Store | SB、SH、SW |
| 位址單位 | Byte addressing；位址加 1 表示前進 1 byte |
| 位元組順序 | Little-endian，低位 byte 放在低位址 |
| 外部資料介面 | 32-bit word 讀寫，4-bit byte enable，請求／回應握手 |
| 自然對齊 | Byte 任意；Halfword 2-byte；Word 4-byte |
| 未對齊處理 | 不拆成多筆交易，發出請求前停止並記錄原始位址 |
| 同時未完成交易 | 全核心最多一筆，包含指令及資料介面 |
| MMIO 規則 | 0x20000000～0x20000FFF 只允許 word 存取；其他位址由外部回應判定可存取性 |
| 完成回報 | 保留 word MMIO 狀態暫存器介面；周邊硬體尚未整合 |
| 例外環境 | 自訂 halt／debug，ECALL／EBREAK 分別停止，未加入標準 trap／CSR／中斷 |

整合版可執行規格中列出的 40 個 RV32I 指令名稱，包含前述整數、控制流程與 FENCE／ECALL／EBREAK 的專案行為。這不代表正式 ISA compliance 認證或完整 machine-mode；此處沒有快取、MMU 或作業系統。

| 指令 | 存取寬度 | 作用 |
| --- | --- | --- |
| LB | 8-bit | 讀取 byte，符號擴展為 32-bit |
| LBU | 8-bit | 讀取 byte，零擴展為 32-bit |
| LH | 16-bit | 讀取 halfword，符號擴展為 32-bit |
| LHU | 16-bit | 讀取 halfword，零擴展為 32-bit |
| LW | 32-bit | 讀取完整 word |
| SB | 8-bit | 寫出 rs2 的低 8-bit |
| SH | 16-bit | 寫出 rs2 的低 16-bit |
| SW | 32-bit | 寫出完整 rs2 |

有效位址都是 `A＋imm`，保留低 32-bit。Load 使用 I-type 符號擴展立即數，Store 使用 S-type；Store 的資料來自 B 保存的 rs2，不是立即數。

## ② 位址、byte lane 與 little-endian

```text
ALUOut＝原始有效位址
    ├→ [31:2] 接上 00 → 外部 dmem_req_addr
    ├→ [1:0] → byte_offset → Load 擷取／Store 排列
    └→ 對齊檢查及 fault_addr（保留原始位址）
```

| 名稱 | 計算 | 例子：有效位址 0x10000003 |
| --- | --- | --- |
| 原始位址 | A＋imm | 0x10000003 |
| word 對齊位址 | {ALUOut[31:2],2'b00} | 0x10000000 |
| byte_offset | ALUOut[1:0] | 3 |
| byte lane | 位址對應的 word 內位置 | lane 3，資料 bits [31:24] |

Little-endian 下，word `0x89ABCDEF` 在連續四個位址的 byte 依序為 EF、CD、AB、89。對齊位址只是外部 word 介面的資料傳遞方式，CPU 原始位址仍是 byte address。

| lane | 位址 | 回應 word 中的 bits | SB 的 wstrb |
| --- | --- | --- | --- |
| 0 | aligned＋0 | [7:0] | 0001 |
| 1 | aligned＋1 | [15:8] | 0010 |
| 2 | aligned＋2 | [23:16] | 0100 |
| 3 | aligned＋3 | [31:24] | 1000 |

## ③ 整合 Datapath 與 MDR

```text
IR → Decoder → mem_size、load_unsigned、wb_sel、instr_class
 │
 └→ imm_gen → I／S 立即數

Register File → A、B
                 │  │
A＋imm → ALU → ALUOut（原始地址）
                    ├→ FSM 對齊檢查 → 對外請求／等待
                    ├→ aligned address → dmem_req_addr
                    └→ byte_offset ───────────────┐
                                                │
B → store_align → dmem_req_wdata／wstrb           │
                                                │
dmem_rsp_data → MDR → load_extract ←─────────────┘
                          │
ALUOut／Load 結果／InstrPC＋4 → Writeback MUX → Register File rd

成功 Load：保存 MDR，下一狀態寫回並更新 PC
成功 Store：收到成功回應時完成並更新 PC，不寫 rd
```

| 保存位置／元件 | 用途 | 更新時機 |
| --- | --- | --- |
| A | 保存 rs1，計算 base＋offset | Decode 的 ab_we |
| B | 保存 rs2，供 Store 寫出 | Decode 的 ab_we |
| ALUOut | 保存原始有效位址 | ADDR_EXEC 的 aluout_we |
| MDR | 32-bit，保存完整原始回應 word | 成功 Load 回應握手的 mdr_we；reset 清 0 |
| load_extract | 根據 offset、size、unsigned 擷取／擴展 MDR | 組合邏輯 |
| store_align | 排列 B 的低 byte／halfword／word，產生 wstrb | 組合邏輯 |
| WB_LOAD | 選取 load_extract 結果 | LOAD_WB 寫回 |

讀取 x0 仍必須發出記憶體交易、處理錯誤，只忽略最後暫存器寫入。JALR 與 Load 的 rd＝rs1 都使用 Decode 保存的 A；寫回不會改變這條指令已保存的位址。

## ④ Load 擷取與擴展規則

先計算 `shifted＝MDR >> (byte_offset×8)`，再依寬度取低位資料。

| 模式 | 結果 |
| --- | --- |
| LB | {{24{shifted[7]}},shifted[7:0]} |
| LBU | {24'b0,shifted[7:0]} |
| LH | {{16{shifted[15]}},shifted[15:0]} |
| LHU | {16'b0,shifted[15:0]} |
| LW | MDR 原始 32-bit word |

本測試第一個 word 是 `0x5B12C980`：byte 依序為 80、C9、12、5B。

| 存取 | 預期結果 |
| --- | --- |
| LB lane 0／LBU lane 0 | FFFFFF80／00000080 |
| LB lane 1／LBU lane 1 | FFFFFFC9／000000C9 |
| LB lane 2／LBU lane 2 | 00000012／00000012 |
| LB lane 3／LBU lane 3 | 0000005B／0000005B |
| LH offset 0／LHU offset 0 | FFFFC980／0000C980 |
| LH offset 2／LHU offset 2 | 00005B12／00005B12 |
| LW offset 0 | 5B12C980 |

擷取模組不發出交易、不判斷存取失敗。FSM 在請求前保證自然對齊；不能把模組在非法 offset 下的組合值當成 CPU 支援未對齊存取。

## ⑤ Store 排列與 byte enable

每個 `wstrb[n]` 對應 `wdata[n*8 +: 8]`，只有啟用的 byte lane 可被記憶體更新。未啟用的 byte 必須保留原值。

以 B＝`0x89ABCDEF`、原 word＝`0x5B12C980` 為例：

| 指令／offset | 對外 wdata | wstrb | 寫入後 word |
| --- | --- | --- | --- |
| SB／0 | 000000EF | 0001 | 5B12C9EF |
| SB／1 | 0000EF00 | 0010 | 5B12EF80 |
| SB／2 | 00EF0000 | 0100 | 5BEFC980 |
| SB／3 | EF000000 | 1000 | EF12C980 |
| SH／0 | 0000CDEF | 0011 | 5B12CDEF |
| SH／2 | CDEF0000 | 1100 | CDEFC980 |
| SW／0 | 89ABCDEF | 1111 | 89ABCDEF |

store_align 對非法 halfword／word offset 輸出零遮罩；真正的錯誤停止仍由 FSM 決定。Load 的對外 wdata／wstrb 為 0，讀取寬度由核心在回應後擷取。

## ⑥ 記憶體握手與 FSM

| 訊號 | 方向 | 寬度 | 定義 |
| --- | --- | --- | --- |
| dmem_req_valid | 輸出 | 1 | 有資料請求；保持直到接受 |
| dmem_req_ready | 輸入 | 1 | 外部可接受請求 |
| dmem_req_write | 輸出 | 1 | 0＝讀，1＝寫 |
| dmem_req_addr | 輸出 | 32 | word 對齊的 byte address |
| dmem_req_wdata | 輸出 | 32 | 已排列的 Store 資料 |
| dmem_req_wstrb | 輸出 | 4 | 要更新的 byte lane |
| dmem_rsp_valid | 輸入 | 1 | 回應有效，包括 Store 的完成回應 |
| dmem_rsp_ready | 輸出 | 1 | 核心能接受回應 |
| dmem_rsp_data | 輸入 | 32 | 完整 word；Load 成功時保存 |
| dmem_rsp_err | 輸入 | 1 | 回應失敗 |

請求在 `req_valid && req_ready` 的上升緣接受；之後 CPU 不重複送出。回應在 `rsp_valid && rsp_ready` 的上升緣完成。請求首次接受的同一個 edge 不處理該交易的回應；外部須將回應資料、error 與 valid 保持到握手。

| 狀態 | 動作 | 正常下一步 |
| --- | --- | --- |
| DECODE | 保存 A／B，選擇 I／S immediate | ADDR_EXEC |
| ADDR_EXEC | A＋imm，保存 ALUOut | MEM_CHECK |
| MEM_CHECK | 檢查對齊、MMIO 寬度，不發交易 | LOAD_WAIT 或 STORE_WAIT |
| LOAD_WAIT，尚未接受 | 發出讀取請求；等待期間保持 payload | 接受後繼續等待回應 |
| LOAD_WAIT，成功回應 | mdr_we＝1，保存完整 word | LOAD_WB |
| LOAD_WB | reg_we、WB_LOAD、pc_we、instr_done | 寫回與 PC＋4，同時回 FETCH |
| STORE_WAIT，尚未接受 | 發出寫入請求；保持 wdata／wstrb | 接受後等待回應 |
| STORE_WAIT，成功回應 | pc_we、instr_done；不写 rd | PC＋4，回 FETCH |
| 回應失敗 | 不寫回、不更新 PC，保存錯誤 | HALTED |

等待期間 IR、A、B、ALUOut、PC 保持；MDR 只在成功 Load 回應時更新。硬體沒有等待逾時機制，testbench 的 timeout 僅用來找模擬卡住。

FENCE 在本架構依序完成，前面的 Load／Store 都已收到回應，沒有待處理寫入緩衝。外部成功回應必須有相符的完成／排序語意；不能只回報「已排隊」卻假設其他主裝置已看到資料。

## ⑦ 錯誤、reset 與副作用界線

| 情況 | halt_cause | fault_addr | 是否發資料請求 |
| --- | --- | --- | --- |
| Load 未對齊 | HALT_LOAD_ALIGN＝4 | 原始有效位址 | 否 |
| Store 未對齊 | HALT_STORE_ALIGN＝5 | 原始有效位址 | 否 |
| MMIO 區窄 Load | HALT_LOAD_ACCESS＝6 | 原始有效位址 | 否 |
| MMIO 區窄 Store | HALT_STORE_ACCESS＝7 | 原始有效位址 | 否 |
| 外部 Load error | HALT_LOAD_ACCESS＝6 | 原始有效位址 | 是 |
| 外部 Store error | HALT_STORE_ACCESS＝7 | 原始有效位址 | 是 |
| 非法 memory 編碼 | HALT_ILLEGAL＝1 | 本專案為 0 | 否 |

fault_pc 指向發生錯誤的 Load／Store 指令，PC 保持該指令位址；對齊錯誤的判斷優先於 MMIO 寬度錯誤。失敗指令沒有正常 commit，也不寫目的暫存器。

**CPU 不會回滾已發生的外部記憶體或 MMIO 副作用。**本測試 endpoint 規定成功 Store 在成功回應握手時生效，失敗 Store 不修改資料；這是測試環境的明確契約，不是 CPU 對任意外部 bus 的保證。

reset 測試讓核心與兩個記憶體模型一起取消 pending／舊回應，並重新初始化測試資料。真實系統要另定外部記憶體 reset／保留內容、交易取消與過期回應處理方式；不能只 reset 核心卻直接使用這個模型的假設。

## ⑧ 完整 RTL

使用這份整合包中的 **11 個 Design Sources**。同名 `fault_v_cpu.sv` 只保留最新一份，其他必要模組都要加入；Testbench 不加入硬體綜合。

'''
for title,file in [('Load 擷取模組','load_extract.sv'),('Store 排列模組','store_align.sv'),('完整 CPU Top','fault_v_cpu.sv')]:
    note+=f'### {title}：{file}\n\n```systemverilog\n'+(root/'rtl'/file).read_text()+'```\n\n'
note+='''## ⑨ 記憶體迴圈範例與預期結果

程式在 0x10000000、04、08、0C 分別存入 1、2、3、4，逐筆讀回並累加。最後的 FENCE 是正常指令，EBREAK 停止。

```asm
'''+(root/'verify/memory_loop.S').read_text()+'''```

| 項目 | 預期結果 |
| --- | --- |
| x5，累加結果 | 10＝0x0000000A |
| x6，最後讀回值 | 4 |
| x2，最後 Store／Load base | 0x1000000C |
| 四個 word | 00000001、00000002、00000003、00000004 |
| 資料交易 | 8 筆：4 次 Store＋4 次 Load |
| 正常 commit／取指 | 29／30 |
| 停止 | PC／fault_pc＝0x48、cause＝9、fault_addr＝0 |

模型中的資料記憶體是 256 bytes，位址為 0x10000000～0x100000FF；另外四個 bytes 在 0x20000000 用作 word MMIO 狀態 stub。這不是最終 16 KiB 記憶體，也不是已完成 UART／GPIO。

## ⑩ 驗證方法與完整 Testbench

| 驗證項目 | 驗收條件 |
| --- | --- |
| 五種 Load | 所有合法 lane、符號／零擴展與資料相依結果正確 |
| 三種 Store | wdata／wstrb 正確，未選中的 byte 保留 |
| 等待與握手 | request 穩定，只接受一次；每筆恰好一個完成回應 |
| 指令／資料介面 | 全核心最多一筆未完成交易 |
| 錯誤 | 未對齊不發請求；失敗不 commit、不寫 rd；原始 fault_addr 正確 |
| x0 | Load x0 仍讀取及處理錯誤；Store x0 寫入零 |
| 程式 | 負偏移、rd＝base、連續讀寫、迴圈與函式讀寫正確 |
| MMIO | 窄存取拒絕、word stub 讀寫及 FENCE 正確 |
| 回歸 | 原整數及控制流程程式的 trace 與最終狀態正確 |
| reset | 已接受 Load／Store 等待時共同 reset，從起點重跑正確 |

軟體預期模型以 byte array 表示記憶體，由指令運算元計算結果與 trace，不讀 DUT、也不照 FSM 的 cycle 安排運作。每個資料 request 都比對位址、方向、資料、遮罩；回應比對 raw word／error；每次 commit 比對指令、PC、寫回與下一個 PC；停止後比對全部 32 個暫存器與全部 260 個模型 bytes。

125 個程式各以兩種延遲執行，另有兩次等待資料回應時 reset 再重跑，共 252 組情境。這是有限的專案功能測試，不是正式 compliance suite 或所有輸入的證明。

`cases_init.svh` 是 testbench 必要的 include，包含完整機器碼與預期表；`cases.json` 保存每個程式的逐次 trace、交易與最終狀態。直接模擬現成檔案不需要先執行 Python。

```systemverilog
'''+(root/'verify/tb_memory_cpu.sv').read_text()+'''```

### 所有程式的預期結果

cause：1＝非法指令、2＝指令對齊、3＝取指失敗、4／5＝Load／Store 對齊、6／7＝Load／Store 存取失敗、8＝ECALL、9＝EBREAK。

| case_id | 程式 | commit | 資料交易 | 停止 PC | cause | fault_addr |
| --- | --- | --- | --- | --- | --- | --- |
'''
for idx,c in enumerate(cases):
    cause,pc,addr=c['stop'];note+=f'| {idx} | {c["name"]} | {len(c["trace"])} | {len(c["tx"])} | `{pc:08X}` | {cause} | `{addr:08X}` |\n'
note+='''
最後兩次 reset 情境重跑記憶體迴圈，預期關鍵輸出：

```text
PASS 251: reset during pending data transaction then restart committed=29 requests=30 pc=00000048 cause=9 data=8
PASS 252: reset during pending data transaction then restart committed=29 requests=30 pc=00000048 cause=9 data=8
ALL 252 MEMORY CPU SCENARIOS PASSED
```

## ⑪ Vivado 使用與檔案配置

1. 解壓縮整合包至一般本機資料夾。
2. Design Sources 加入 `rtl` 內 11 個 `.sv`。`fault_v_pkg.sv` 先編譯，避免同時加入舊版本的同名檔案。
3. Simulation Sources 加入 `verify/tb_memory_cpu.sv` 與 `verify/cases_init.svh`。找不到 include 時，把 `verify` 的完整路徑加入 Simulation Include Directories。
4. Simulation Top 設為 **tb_memory_cpu**；Design Top 是 **fault_v_cpu**。
5. 執行 Behavioral Simulation，Tcl Console 輸入 **run all**；1000 ns 不足以跑完。
6. 確認最後的 `ALL 252 MEMORY CPU SCENARIOS PASSED`、正常 `$finish`，沒有 Fatal。

| 檔案 | 用途 |
| --- | --- |
| rtl/fault_v_cpu.sv | 整合運算、控制流程及資料讀寫的 CPU Top |
| rtl/load_extract.sv／store_align.sv | 讀回擷取／擴展、寫出資料／遮罩 |
| rtl 其他八檔 | ALU、imm_gen、RegFile、PC、Decoder、FSM、Branch Comparator、package |
| verify/tb_memory_cpu.sv／cases_init.svh | 模擬環境與完整預期表 |
| verify/memory_loop.S／memory_loop.mem | 可閱讀程式與對應機器碼 |
| cases.json | 全部程式、預期 trace、交易、暫存器與記憶體 |
| reference_model.py／build_cases.py／make_tb.py | 重產生預期資料與 testbench 的 Python 工具 |
| reference_inputs | 回歸資料與模板；不加入 Simulation Sources |
| run_xsim.ps1 | XSim 編譯、elaboration、模擬及 PASS 檢查 |
| logs/memory_cpu_results.log | 獨立模擬證據 |

也可在 PowerShell 執行 `run_xsim.ps1`；預設 Vivado 2022.2 路徑，可傳入 `-VivadoBin` 調整。若要重產生測試資料，依序執行 `python build_cases.py`、`python make_tb.py`。

這份 RTL 是後續整合的基礎，還要加入實際記憶體、載入程式方式、UART／GPIO、clock／reset 與 FPGA 約束。功能模擬的 10 ns clock 不代表硬體已達到 100 MHz；本文件沒有宣稱 FPGA 時序、實板或 ASIC sign-off 通過。
'''
note=note.replace('不写','不寫')
(root/'Load_Store_CPU_Notion.md').write_text(note,encoding='utf-8')
(root/'verify/memory_loop.mem').write_text('\n'.join(f'{w:08x}' for w in cases[87]['words'])+'\n')
