from pathlib import Path
import json,re,shutil,zipfile,hashlib
root=Path(__file__).resolve().parent
parts=[]
def add(s):parts.append(s.strip()+'\n')
def code(p):add('```systemverilog\n'+(root/p).read_text(encoding='utf-8-sig').rstrip()+'\n```')
add('''# Fault-V｜Control FSM：多周期控制器

**① 模組用途與規格**

Control FSM 根據 Decoder 的分類與記憶體回應，把一條指令拆成多個 clock cycle，產生資料路徑的寫入允許、記憶體握手與錯誤停止控制。

| 項目 | 規格 |
| --- | --- |
| 模組名稱 | control_fsm |
| 核心執行方式 | 32-bit、多周期、一次一條指令、依序完成 |
| Clock | 單一 clock，上升緣更新 |
| Reset | 高有效、同步重置狀態與除錯暫存器；rst 高時組合控制輸出立即停用 |
| 狀態 | 15 個狀態，內部控制型別為 4-bit |
| 記憶體介面 | 指令／資料分離的 request／response 握手 |
| 未完成交易數 | 全核心最多一筆 |
| PC 更新 | 只在指令正常完成時更新 |
| 錯誤策略 | 阻擋該指令提交，保存原因與位址，進入 HALTED |
| 恢復方式 | Reset |
| 硬體 timeout | 本版沒有；外部不回應時維持等待 |

Decoder 的 rd_write 表示「需要寫回」；FSM 的 reg_we 表示「這一拍允許寫回」。两者不能直接混用。

---

**② 模組責任與資料保存**

| 位置 | 保存／處理內容 |
| --- | --- |
| FSM 內部 | State、mem_pending、halt_cause、fault_pc、fault_addr |
| 外部 PC | 下一次取指地址；正常提交時才更新 |
| 外部 IR／InstrPC | 目前指令與它的原始地址；成功取指時同時保存 |
| 外部 A／B | Decode 階段保存 Register File 的兩個讀取值 |
| 外部 ALUOut | Execute 階段保存運算結果、有效位址或處理後跳躍目標 |
| 外部 BranchTaken | BR_EXEC 階段保存比較器結果 |
| 外部 MDR | 成功 Load 回應時保存原始對齊 word |
| 外部 Load／Store 處理 | byte 擷取與擴展、Store 資料移位與四位元 byte enable |

本版對齊與初始 MMIO 存取寬度檢查放在 FSM 的 MEM_CHECK，和請求控制一起判斷。ALU、位址加法、分支比較與資料擴展仍在資料路徑。

IR、InstrPC 與 Decoder 輸出在指令執行期間保持不變。ALUOut、BranchTaken、A、B、MDR 都必須由对应 enable 更新，不能每拍無條件覆寫。

---

**③ 輸入介面**

| 訊號 | 寬度／型別 | 說明 |
| --- | --- | --- |
| clk／rst | 各 1-bit | Clock 與高有效 reset |
| instr_class | instr_class_t／4-bit | Decoder 分類 |
| illegal | 1-bit | Decoder 判定非法／未支援 |
| rd_write | 1-bit | Decoder 的寫回需求 |
| mem_size | mem_size_t／2-bit | Byte／Halfword／Word |
| pc | 32-bit | 目前取指位址 |
| instr_pc | 32-bit | IR 這條指令的位址 |
| mem_addr | 32-bit | ALUOut 保存的原始資料有效位址 |
| target_addr | 32-bit | ALUOut 保存的目標；JALR 已在外部清除 bit 0 |
| branch_taken | 1-bit | BranchTaken 暫存器的值 |
| imem_req_ready | 1-bit | 指令端接受請求 |
| imem_rsp_valid／imem_rsp_err | 各 1-bit | 指令回應有效／錯誤 |
| dmem_req_ready | 1-bit | 資料端接受請求 |
| dmem_rsp_valid／dmem_rsp_err | 各 1-bit | 資料回應有效／錯誤 |

指令與讀回資料直接送往外部 IR／MDR，不經由 control_fsm 的資料輸入埠。Decoder 的 alu_op、imm_sel、輸入來源與 wb_sel 也直接接到資料路徑；FSM 產生更新時機。

---

**④ 輸出介面**

| 訊號 | 寬度／型別 | 說明 |
| --- | --- | --- |
| imem_req_valid | 1-bit | 取指請求有效 |
| imem_req_addr | 32-bit | PC，不進行額外地址轉換 |
| imem_rsp_ready | 1-bit | 接受当前取指回應 |
| dmem_req_valid | 1-bit | 資料請求有效 |
| dmem_req_addr | 32-bit | mem_addr 清除低兩位後的對齊 word 地址 |
| dmem_req_write | 1-bit | 資料交易為 Store；只在 req_valid 有效時使用 |
| dmem_rsp_ready | 1-bit | 接受当前資料回應 |
| ir_we／instr_pc_we | 各 1-bit | 同一拍保存指令與取指 PC |
| ab_we | 1-bit | 同一拍保存兩個讀取運算元 |
| aluout_we | 1-bit | 保存 ALU／JALR 處理後結果 |
| branch_taken_we | 1-bit | 保存分支條件 |
| mdr_we | 1-bit | 保存成功 Load 回應 |
| reg_we | 1-bit | 接 Register File 的 rd_we |
| pc_we | 1-bit | 接 PC 暫存器的更新允許 |
| pc_sel | pc_sel_t／1-bit | PC_SEQ＝InstrPC＋4；PC_TARGET＝ALUOut |
| instr_done | 1-bit | 該指令在這個上升緣正常完成；本版等於 pc_we |
| state | cpu_state_t／4-bit | 供模擬與除錯觀察 |
| mem_pending | 1-bit | 已接受請求，尚未接受完成回應 |
| halted | 1-bit | State＝HALTED |
| halt_cause | halt_cause_t／4-bit | 保存的停止原因 |
| fault_pc／fault_addr | 各 32-bit | 保存的指令位址／相關地址 |

dmem_req_wdata 與 dmem_req_wstrb 由 Store 對齊邏輯產生。Store 請求等待時，這兩個訊號必须和地址、write 一樣保持穩定。

---

**⑤ 共用狀態與編碼：fault_v_pkg.sv**

以下保留既有 ALU、IMM 與 Decoder 編碼，加入 FSM 狀態、PC 選擇與停止原因。專案只使用一份同名 package。
''')
code('rtl/fault_v_pkg.sv')
add('''---

**⑥ 狀態圖**

```mermaid
flowchart TD
    FETCH[FETCH：取指請求與等待] -->|成功回應| DECODE[DECODE]
    FETCH -->|請求未接受或回應未到| FETCH
    DECODE --> ALU_EXEC[ALU_EXEC]
    ALU_EXEC --> ALU_WB[ALU_WB：寫回與 PC 更新]
    ALU_WB --> FETCH
    DECODE --> ADDR_EXEC[ADDR_EXEC]
    ADDR_EXEC --> MEM_CHECK[MEM_CHECK：對齊及 MMIO 檢查]
    MEM_CHECK --> LOAD_WAIT[LOAD_WAIT]
    MEM_CHECK --> STORE_WAIT[STORE_WAIT]
    LOAD_WAIT -->|等待| LOAD_WAIT
    STORE_WAIT -->|等待| STORE_WAIT
    LOAD_WAIT -->|成功回應| LOAD_WB[LOAD_WB：寫回與 PC 更新]
    LOAD_WB --> FETCH
    STORE_WAIT -->|成功回應且更新 PC| FETCH
    DECODE --> BR_EXEC[BR_EXEC：目標與條件保存]
    BR_EXEC --> BR_COMMIT[BR_COMMIT：選擇 PC]
    BR_COMMIT --> FETCH
    DECODE --> JUMP_EXEC[JUMP_EXEC：目標保存]
    JUMP_EXEC --> JUMP_COMMIT[JUMP_COMMIT：返回位址與 PC]
    JUMP_COMMIT --> FETCH
    DECODE --> FENCE_COMMIT[FENCE_COMMIT]
    FENCE_COMMIT -->|無未完成存取| FETCH
    ERROR[非法、錯誤、ECALL、EBREAK] --> HALTED[HALTED：保存原因並保持]
    HALTED --> HALTED
```

任一錯誤路徑依下一節規則轉至 HALTED；圖中的 ERROR 是說明節點，不是額外的 RTL 狀態。Reset 後回到 FETCH。

---

**⑦ 逐狀態控制表**

未列出的 enable 皆為 0。所有動作在 clock 上升緣生效，條件满足時才啟用。

| 狀態 | 有效動作 | 轉移條件／下一狀態 |
| --- | --- | --- |
| FETCH，pending＝0 | 對齊且非 reset 時 imem_req_valid＝1 | req_valid＆req_ready：pending＝1，仍在 FETCH |
| FETCH，pending＝1 | imem_rsp_ready＝1 | 成功回應：ir_we、instr_pc_we＝1，pending＝0 → DECODE；失敗 → HALTED |
| DECODE | 運算／存取／分支／跳躍時 ab_we＝1 | 按 instr_class 分流；illegal 優先停止 |
| ALU_EXEC | aluout_we＝1 | → ALU_WB |
| ALU_WB | reg_we＝rd_write、pc_we＝1、PC_SEQ、instr_done＝1 | → FETCH |
| ADDR_EXEC | aluout_we＝1 | → MEM_CHECK |
| MEM_CHECK | 檢查原始有效位址，不發請求 | 合法 Load → LOAD_WAIT；合法 Store → STORE_WAIT；錯誤 → HALTED |
| LOAD_WAIT，pending＝0 | dmem_req_valid＝1、write＝0 | 請求接受後 pending＝1，保持 |
| LOAD_WAIT，pending＝1 | dmem_rsp_ready＝1 | 成功：mdr_we＝1、pending＝0 → LOAD_WB；失敗 → HALTED |
| LOAD_WB | reg_we＝rd_write、pc_we＝1、PC_SEQ、instr_done＝1 | → FETCH |
| STORE_WAIT，pending＝0 | dmem_req_valid＝1、write＝1 | 請求接受後 pending＝1，保持 |
| STORE_WAIT，pending＝1 | dmem_rsp_ready＝1 | 成功：pending＝0、pc_we＝1、PC_SEQ、instr_done＝1 → FETCH；失敗 → HALTED |
| BR_EXEC | aluout_we、branch_taken_we＝1 | → BR_COMMIT |
| BR_COMMIT | 未錯誤時 pc_we、instr_done＝1；不寫回 RF | 成立選 PC_TARGET；不成立選 PC_SEQ → FETCH |
| JUMP_EXEC | aluout_we＝1 | → JUMP_COMMIT |
| JUMP_COMMIT | 目標對齊時 reg_we＝rd_write、pc_we＝1、PC_TARGET、instr_done＝1 | → FETCH；未對齊 → HALTED |
| FENCE_COMMIT | pending＝0 時 pc_we、instr_done＝1、PC_SEQ | → FETCH；否則等待 |
| HALTED | 不再發請求、不接受新回應、不寫入資料路徑 | 保持；Reset 恢復 |

錯誤回應發生的當拍仍保留該回應通道的 rsp_ready，先把錯誤回應接受完，清除 pending，再在上升緣進入 HALTED。

---

**⑧ 記憶體握手與等待規則**

| 項目 | 規則 |
| --- | --- |
| 請求接受 | req_valid＆req_ready 在上升緣同為 1 |
| 等待接受 | req_valid 保持 1；請求內容保持穩定 |
| 已接受請求 | mem_pending＝1；req_valid 轉為 0 |
| 回應接受 | 對應 rsp_valid＆rsp_ready 在上升緣同為 1 |
| 回應等待 | 記憶體端保持 rsp_valid、data、err，直到回應被接受 |
| 完成回應 | 包含 Store 的成功／失敗回應；不是只有 Load 才要回應 |
| 同一邊緣請求與回應 | 本控制器不在請求接受的同一個邊緣接受該筆回應 |
| 無已接受請求時的回應 | rsp_ready＝0，不接受 |
| 通道所有權 | FETCH 只接受指令回應；LOAD_WAIT／STORE_WAIT 只接受資料回應 |
| 重送 | 成功或失敗回應后皆不自動重送 |

```text
                請求尚未被接受       已接受，等待回應       回應被接受
req_valid           1  1  1                 0                    0
req_ready           0  0  1                 X                    X
mem_pending         0  0  0                 1              下一拍變 0
rsp_ready           0  0  0                 1                    1
rsp_valid           0  0  0             0 ... 0                    1
```

X 表示本次請求完成接受後，不再使用 req_ready 的值。回應若提早出现，也必須保持到 rsp_ready 為 1，不能只送一個未被接受的脈衝。

mem_pending 和狀態一起保存，因此 response valid 不能被當成「每拍都可執行的寫回事件」。控制器只在正確等待狀態接受一次。

---

**⑨ PC、寫回與提交規則**

| 指令／情況 | 更新 PC | 寫回 RF |
| --- | --- | --- |
| 運算指令 | ALU_WB：InstrPC＋4 | ALUOut |
| Load | LOAD_WB：InstrPC＋4 | MDR 擷取／擴展後資料 |
| Store | 成功完成回應的邊緣：InstrPC＋4 | 無 |
| Branch 不成立 | BR_COMMIT：InstrPC＋4 | 無 |
| Branch 成立且目標對齊 | BR_COMMIT：ALUOut | 無 |
| JAL／JALR 目標對齊 | JUMP_COMMIT：ALUOut | InstrPC＋4 |
| FENCE | FENCE_COMMIT：InstrPC＋4 | 無 |
| 等待／錯誤／ECALL／EBREAK | 不更新 | 不寫入 |

instr_done 在正常完成的邊緣有效，用於測試計數；本版取指、Decode、Execute、等待以及停止都不令它有效。

rd＝x0 時 reg_we 可以為 1，Register File 會忽略該寫入。Load 到 x0 仍完整执行存取與錯誤處理。

---

**⑩ 對齊與 MMIO 規則**

| 存取 | 檢查 |
| --- | --- |
| 取指 | PC[1:0] 必須為 00，否則不發請求 |
| 採用的 Branch／Jump 目標 | target_addr[1:0] 必須為 00 |
| 未採用的 Branch 目標 | 不檢查目標對齊 |
| Byte | 任意有效位址低兩位皆可 |
| Halfword | mem_addr[0] 必須為 0 |
| Word | mem_addr[1:0] 必須為 00 |
| 初始 MMIO 頁 | 0x20000000～0x20000FFF，只允許 Word 存取 |

JALR 必須先在外部清除結果 bit 0，保存到 ALUOut，再由 JUMP_COMMIT 檢查是否满足 4-byte 對齊。例如原始目標 0x103 清除后為 0x102，仍會停止。

MEM_CHECK 先判斷資料未對齊，再判斷 MMIO 寬度，所以 MMIO 的未對齊 halfword 優先回報未對齊原因。

對外 dmem_req_addr＝mem_addr＆0xFFFFFFFC。Load 擷取與 Store mask、資料移位仍使用原始 mem_addr[1:0]；fault_addr 也保存原始位址。

控制器不在這裡限制全部合法記憶體區域。除了已定義的窄 MMIO 禁止規則，未映射／唯讀／超出容量等存取由記憶體互連或周邊用 rsp_err 回報。改变記憶體配置時，应同步更新檢查規格。

---

**⑪ 停止原因與保存資訊**

| 原因 | 編碼 | fault_pc | fault_addr |
| --- | --- | --- | --- |
| NONE | 0 | Reset 清 0 | Reset 清 0 |
| ILLEGAL | 1 | InstrPC | 0 |
| INSTR_ALIGN：取指 | 2 | PC | PC |
| INSTR_ALIGN：Branch／Jump | 2 | InstrPC | 處理後目標 |
| FETCH_ACCESS | 3 | PC | PC |
| LOAD_ALIGN | 4 | InstrPC | 原始 mem_addr |
| STORE_ALIGN | 5 | InstrPC | 原始 mem_addr |
| LOAD_ACCESS | 6 | InstrPC | 原始 mem_addr |
| STORE_ACCESS | 7 | InstrPC | 原始 mem_addr |
| ECALL | 8 | InstrPC | 0 |
| EBREAK | 9 | InstrPC | 0 |
| INTERNAL | 10 | InstrPC | 0 |

INTERNAL 是額外的控制器診斷值，用於無效狀態或 MEM_CHECK 中不符合预期的指令分類；原有原因的 0～9 編碼保留。這個預設分支不等於已具備硬體故障容錯能力。

Debug 資訊在進入 HALTED 的上升緣保存，之后保持到 Reset。HALTED 中输入改變不會繼續執行，也不會覆寫停止原因。

Store 被接受後，外部可能已产生副作用。失敗回應或 reset 不保證回復已寫入記憶體／周邊的狀態，控制器不自動重試。

如果跳躍已经提交，下一次目標取指才失敗，錯誤屬於目標 PC；已寫入的返回位址會保留。

---

**⑫ Reset 與外部介面約定**

| 項目 | 行為／要求 |
| --- | --- |
| rst 拉高、邊緣尚未到 | State 與 debug 保存值暫時不變；請求、回應 ready 與寫入 enable 停用 |
| rst＝1 的上升緣 | State→FETCH、pending→0、停止資訊清 0 |
| PC／RF／資料路徑 | 必須使用同一個適當同步的 reset |
| 記憶體與周邊控制介面 | Reset 取消未完成的請求／回應追蹤，不再返回舊交易回應 |
| SRAM 内容／已發生副作用 | 不要求因 reset 自動回復 |
| Reset 解除 | 由重置后的 PC 重新取指 |

本介面沒有 transaction ID，不能區分 reset 前與 reset 后交易。外部橋接器若不能取消舊交易，必須在解除核心 reset 前先排空或隔離它們。

---

**⑬ 完整 RTL：control_fsm.sv**
''')
code('rtl/control_fsm.sv')
add('''---

**⑭ 最短正常執行時序範例**

假設每個請求立即被接受，記憶體回應在下一個边緣接受。下面的 C1、C2 是連續 clock 上升緣，不是學習日期。

| 指令類別 | 邊緣上的動作 | 最短 cycle 數 |
| --- | --- | --- |
| ALU／LUI／AUIPC | C1 取指接受 → C2 IR 保存 → C3 A/B 保存 → C4 ALUOut 保存 → C5 寫回／PC | 5 |
| Branch | C1 取指 → C2 IR → C3 A/B → C4 目標／BranchTaken → C5 PC | 5 |
| JAL／JALR | C1 取指 → C2 IR → C3 A/B → C4 目標 → C5 返回位址／PC | 5 |
| Load | C1 取指 → C2 IR → C3 A/B → C4 有效位址 → C5 檢查 → C6 資料請求 → C7 MDR → C8 寫回／PC | 8 |
| Store | C1 取指 → C2 IR → C3 A/B → C4 有效位址 → C5 檢查 → C6 資料請求 → C7 成功回應／PC | 7 |
| FENCE | C1 取指 → C2 IR → C3 分類 → C4 確認無 pending／PC | 4 |

記憶體接受／回應每多等待一拍，執行時間就增加一拍。testbench 的記憶體模型可能額外註冊 ready，因此觀察到的時長不一定是這個最短值。

---

**⑮ 控制器單元驗證方法**

tb_control_fsm 直接提供 Decoder 分類與資料路徑狀態，核對 FSM 各狀態的 enable、轉移與停止資訊。

| 測試範圍 | 檢查內容 |
| --- | --- |
| 取指與資料等待 | 请求／回應延遲各 0～3，確認 pending 與請求只接受一次 |
| ALU、Load、Store | 正確分流、執行與提交 |
| Branch | 成立／不成立／未採用未對齊目標／採用未對齊目標 |
| Jump | JAL、JALR 的目標檢查與返回位址寫入允許 |
| 特殊／非法 | FENCE、ECALL、EBREAK、非法優先權 |
| 存取失敗 | 取指、Load、Store 的錯誤回應握手与 pending 清除 |
| 資料對齊與 MMIO | Halfword／Word 錯誤、窄 MMIO、錯誤優先順序與原始位址保存 |
| Reset | 自然到達所有 15 個狀態後重置；另外重置已接受的取指與資料交易 |
| HALTED | 保持停止、不產生後續寫入／請求、debug 不被外部输入變更覆寫 |

獨立 monitor 以實際握手維護交易計數，確認 mem_pending 和它一致；也检查地址在背壓期間不變、IR／MDR 只在成功回應時更新、RF 只在合法提交狀態寫入。

---

**⑯ 完整單元 Testbench：tb_control_fsm.sv**
''')
code('verify/tb_control_fsm.sv')
add('''---

**⑰ 模擬資料路徑整合方法**

tb_control_path 連接真正的 Decoder、Immediate Generator、ALU、Register File、PC 暫存器與 control_fsm。

IR／InstrPC／A／B／ALUOut／MDR／BranchTaken、輸入 MUX、分支比較、Load 擴展、Store mask 和寫回選擇在 testbench 中依規格接線。這是驗證用資料路徑；正式 CPU top 要把這些可綜合邏輯整理成設計模組，移除測試初始化與記憶體替身。

| 測試條件 | 設定 |
| --- | --- |
| 每個指定案例的起始 PC | Reset PC＝0 |
| 運算元初始化 | 經實際 Register File 寫入埠设置 x6／x7，仅用於測試 |
| 指令記憶體 | 提供該筆固定指令與完成回應，不是完整程式 ROM |
| 資料讀回 word | 0x80FF7F01，Little-endian |
| 資料端延遲 | 每個案例改變請求／回應延遲 |
| Store | 捕捉一次接受的地址、資料與 byte mask |
| RF 驗證 | 核對寫入次數、目的與值，并讀回真正 Register File |
| x0 | 每個案例確認仍為零 |

Little-endian 的 0x80FF7F01 对應 offset 0～3 的 byte：01、7F、FF、80。因此 LB offset 3 得到 FFFFFF80，LBU 得到 00000080；LH offset 2 得到 FFFF80FF，LHU 得到 000080FF。

Store 的低位資料依 offset 左移。SB 在 offset 3，B＝A1B2C3D4 时，對外 data＝D4000000、mask＝8；SH 在 offset 2，data＝C3D40000、mask＝C。

---

**⑱ 完整整合 Testbench：tb_control_path.sv**
''')
code('verify/tb_control_path.sv')
add('''---

**⑲ 指定案例的預期結果**

此表是測試規格。PC、寫回值、fault_addr 為十六進位；原因值對照停止原因表。RF 次數只計入非 x0 的 CPU 寫入，排除測試初始化。實際執行證據另外保存在驗證紀錄。

| 編號 | 案例 | 最後 PC | RF 寫入次數 | RF 寫回值 | 資料請求數 | 停止原因 | fault_addr |
| --- | --- | --- | --- | --- | --- | --- | --- |''')
cases=json.loads((root/'case_spec.json').read_text(encoding='utf-8'))
causes={'HALT_NONE':0,'HALT_ILLEGAL':1,'HALT_INSTR_ALIGN':2,'HALT_FETCH_ACCESS':3,'HALT_LOAD_ALIGN':4,'HALT_STORE_ALIGN':5,'HALT_LOAD_ACCESS':6,'HALT_STORE_ACCESS':7,'HALT_ECALL':8,'HALT_EBREAK':9}
for idx,(n,inst,av,bv,wr,wb,pc,cause,fa,req,err,bus,store,mask) in enumerate(cases,1):
    add(f'| {idx} | {n} | `{pc:08X}` | {wr} | `{wb:08X}` | {req} | {causes[cause]} | `{fa:08X}` |')
add('''| 76 | 跳躍提交後，目標取指失敗 | `00000010` | 1，先前跳躍 | `00000004` | 0 | 3 | `00000010` |

第 76 筆还確認 fault_pc＝0x10，x5 中先前寫入的返回位址＝4，已提交指令數仍為 1。

---

**⑳ Vivado 檔案設定與預期輸出**

| 用途 | 檔案 | 加入位置 |
| --- | --- | --- |
| 共用型別 | fault_v_pkg.sv | Design Sources，唯一一份，編譯在前 |
| 控制器 | control_fsm.sv | Design Sources |
| 整合既有模組 | decoder.sv、alu.sv、imm_gen.sv、regfile.sv、pc_reg.sv | Design Sources，已有同名模組時沿用或一致替換 |
| 控制器單元測試 | tb_control_fsm.sv | Simulation Sources |
| 資料路徑整合測試 | tb_control_path.sv | Simulation Sources |

檔案類型設為 SystemVerilog。切換測試時先 Close Simulation，再對所需 testbench 右鍵 → Set as Top → Run Behavioral Simulation。

Tcl Console 使用：

```tcl
run all
```

單元測試預期最後顯示：

```text
ALL 92 CONTROL FSM SCENARIOS PASSED (5626 checks)
$finish called at time : 9836 ns
```

整合測試預期最後顯示：

```text
ALL 76 CONTROL PATH CASES PASSED
$finish called at time : 11051 ns
```

兩者都超过默认的 1000 ns，所以應用 Run All。測試有 watchdog；回應遗失或狀態不前進時會 $fatal，而不是把部分 PASS 當成整份測試成功。

---

**㉑ 驗收標準與設計交付界線**

| 項目 | 驗收要求 |
| --- | --- |
| 指令控制 | 所有已支援分類走正確路徑，寫入允許符合狀態表 |
| 記憶體協定 | 背壓時請求穩定；每次接受一筆；回應只能消耗一次 |
| 讀回／寫回 | 成功 Load 先保存 MDR，再在 LOAD_WB 寫回；失敗不寫回 |
| PC／返回位址 | 正常完成才更新；未對齊目標不提交；下一次取指失敗不回復之前跳躍 |
| 錯誤停止 | 各原因及位址正確，HALTED 保持，直到 reset |
| Reset | 所有狀態与 pending 交易可重置；外部满足共同 reset 協定 |
| 與 Decoder 相容 | 保留已定義的型別與原編碼，原模組測試持續通過 |
| RTL 綜合 | control_fsm 可綜合，沒有非預期 latch 或黑盒 |
| 最終 CPU 整合 | 正式 top、完整記憶體／周邊、程式級驗證另行接入與核對 |

control_fsm 是可綜合控制器。測試中的資料路徑與記憶體替身提供控制驗證環境；CPU 的程式執行、FPGA 實板、完整約束下的時序與 ASIC 流程，各自需要对应整合驗證。

---

**㉒ 隨附檔案與接線方式**

| 位置 | 內容 |
| --- | --- |
| Control_FSM_Notion.md | 模組技術筆記、完整 RTL 與兩份 testbench |
| Control_FSM_Verification.md | 實際工具執行紀錄、結果與驗證範圍 |
| rtl/ | 新控制器、更新 package、重現所需既有模組 |
| verify/ | 两個新測試與既有模組回歸測試 |
| logs/ | XSim 與綜合原始輸出 |
| run_xsim.ps1 | 預設 Vivado 2022.2 的命令列重現腳本 |
| check_synthesis.tcl | 控制器單獨綜合與 latch 檢查 |

接線要點：

1. 原專案只保留一份更新后的 fault_v_pkg。
2. ir_we 同時更新 IR；instr_pc_we 把当前 PC 保存到 InstrPC。
3. ab_we 接 A/B；aluout_we 接 ALUOut；mdr_we 接 MDR。
4. branch_taken_we 接 BranchTaken；target_addr 接已處理 JALR 的 ALUOut。
5. reg_we 接 Register File 的 rd_we，目的地址仍来自 Decoder 的 rd_addr。
6. pc_we 接 PC，pc_sel 控制 InstrPC＋4／ALUOut。
7. 外部存取資料與 strobe 在等待時保持，rsp_err 隨有效回應提供。

正式 CPU 不需要再串上一個獨立 pc_path 控制器；其已驗證的目標與 PC 選擇功能应整理進共同 Datapath，由這一個 FSM 統一控制。
''')

text='\n'.join(parts)
text=re.sub(r'(?m)(\|[^\n]*\|)\n\n(?=\|)',r'\1\n',text)
replacements={'两':'兩','对应':'對應','当前':'目前','必须':'必須','满足':'滿足','后':'後','出现':'出現','执行':'執行','改变':'改變','应':'應','预期':'預期','之后':'之後','输入':'輸入','产生':'產生','已经':'已經','请求':'請求','检查':'檢查','设置':'設定','仅':'僅','并':'並','对應':'對應','时':'時','还':'還','超过':'超過','默认':'預設','遗失':'遺失','与':'與','来自':'來自'}
for a,b in replacements.items():text=text.replace(a,b)
(root/'Control_FSM_Notion.md').write_text(text,encoding='utf-8')

log_names=['control_fsm_results.log','control_path_results.log','tb_decoder_results.log','tb_decode_path_results.log','tb_alu_results.log','tb_imm_gen_results.log','tb_regfile_results.log','tb_pc_reg_results.log','tb_pc_path_results.log']
observed=[]
for name in log_names:
    p=root/'sim'/name
    if not p.exists():raise RuntimeError('Missing log '+name)
    txt=p.read_text(encoding='utf-8',errors='replace')
    if re.search(r'(?m)^Fatal:|^ERROR:|FAIL |TIMEOUT ',txt):raise RuntimeError('Failed '+name)
    marker=re.search(r'ALL \d+ .* PASSED[^\r\n]*',txt)
    finish=re.search(r'\$finish called at time\s*:\s*(\d+) ns',txt)
    if not marker or not finish:raise RuntimeError('Incomplete '+name)
    observed.append((name,marker.group(),finish.group(1)))
    shutil.copyfile(p,root/'logs'/name)

report='''# Fault-V｜Control FSM 驗證紀錄

工具：Vivado 2022.2 XSim；驗證日期：2026-10-05（台灣）。驗證在獨立 control_fsm 資料夾執行，Downloads/fault-V 原專案未被修改。

**① 功能模擬結果**

| 執行紀錄 | 完成訊息 | 結束時間 |
| --- | --- | --- |
'''
for name,marker,t in observed:report+=f'| {name} | `{marker}` | {t} ns |\n'
report+='''
控制器單元測試包含 92 個情境、5,626 次明確檢查；整合測試包含 76 個案例。各測試以完成標記及無 Fatal／FAIL／TIMEOUT 判定，不能只用 xsim 程序退出碼判断。

**② 驗證內容與實際界線**

單元測試核對狀態／控制輸出、握手追蹤、0～3 拍請求與回應等待、錯誤停止、原始 fault_addr、所有 15 狀態的 reset，以及接受交易後的 reset。

整合測試使用真正 Decoder、ALU、imm_gen、RF、PC、FSM；testbench 接出中間暫存器與資料處理，透過固定指令與記憶體替身驗證 40 種基本指令名稱、六種分支的正反條件、跳躍、Load 擴展、Store mask、MMIO 規則與錯誤。額外確認跳躍後的目標取指失敗不回復已提交返回位址。

回歸測試使用更新後 package 重新編譯所有既有模組與 testbench。

尚未進行所有資料組合／形式驗證、HALT_INTERNAL 硬體故障注入、完整程式執行、真實 SRAM／UART／GPIO 互連、實板與 ASIC 驗證。外部共同 reset／無舊回應的約定仍需在正式互連中落實。

**③ 綜合檢查**

SYNTHESIS_INSERT

**④ 重現與檔案一致性**

在解壓後的資料夾可使用 run_xsim.ps1；預設工具位置 C:/Xilinx/Vivado/2022.2/bin，可透過 -VivadoBin 指定其他安裝位置。只重跑既有模組可加 -RegressionOnly。

技術筆記包含兩份新測試的完整程式；logs/ 提供實際執行輸出。

以下 SHA-256 針對本次交付的設計與新測試：

| 檔案 | SHA-256 |
| --- | --- |
'''
synth=(root/'logs/synthesis.log').read_text(encoding='utf-8',errors='replace')
if 'CONTROL FSM SYNTHESIS PASSED; inferred_latches=0' in synth:
    detail='''control_fsm 單獨以 xc7z020clg400-1 做 out-of-context 綜合。工具完成網表生成與零 latch 檢查，利用率報告位於 logs/control_fsm_utilization.rpt。

這是控制器單獨綜合，沒有完整 CPU、I/O 約束或 clock timing 約束，沒有宣稱 FPGA 時序／ASIC 時序已通過。常數 dmem_req_addr[1:0]＝0 是字對齊設計的預期結果。工具啟動時的 Tcl store 寫入權限訊息屬安裝環境警告，原始輸出保留在 synthesis.log。'''
else:
    detail='''功能模擬全部通過。額外執行 control_fsm 的 xc7z020clg400-1 out-of-context 綜合時，Vivado 已進入網表生成並輸出 cell 統計，但最後清理 .Xil/.../realtime/tmp 時報「no such file or directory」，導致 synth_design 回傳失敗。嘗試較短工作路徑與預建暫存目錄後仍遇到同一類工具檔案系統問題。

因此本次不記錄完整綜合通過、零 latch 檢查通過或可用 synthesis checkpoint；中途的 73 個 FDRE 等統計不能替代最後驗收。synthesis.log 保留失敗與查詢可用設計的診斷輸出。提供的 check_synthesis.tcl 是正常綜合與結構檢查腳本，遇到失敗會停止，不會忽略錯誤當成通過。

此項不影響已完成的 XSim 功能測試。FPGA 完整時序、實板與 ASIC 驗證仍需在各自整合環境執行。'''
report=report.replace('SYNTHESIS_INSERT',detail)
for p in [root/'rtl/fault_v_pkg.sv',root/'rtl/control_fsm.sv',root/'verify/tb_control_fsm.sv',root/'verify/tb_control_path.sv']:
    report+=f'| {p.relative_to(root).as_posix()} | `{hashlib.sha256(p.read_bytes()).hexdigest()}` |\n'
(root/'Control_FSM_Verification.md').write_text(report,encoding='utf-8')
with zipfile.ZipFile(root.parent/'Fault-V_Control_FSM.zip','w',zipfile.ZIP_DEFLATED) as z:
    for folder in ['rtl','verify','logs']:
        for f in sorted((root/folder).glob('*')):
            if f.is_file():z.write(f,'Fault-V_Control_FSM/'+f.relative_to(root).as_posix())
    for name in ['Control_FSM_Notion.md','Control_FSM_Verification.md','run_xsim.ps1','check_synthesis.tcl']:
        z.write(root/name,'Fault-V_Control_FSM/'+name)
print('Built technology notes, separate verification report, and source bundle.')
print('Synthesis successful:', 'CONTROL FSM SYNTHESIS PASSED; inferred_latches=0' in synth)
