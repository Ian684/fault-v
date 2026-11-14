from pathlib import Path
import json
from isa_model import rr,ii,sizes,preds
root=Path(__file__).resolve().parent
cases=json.loads((root/'suite.json').read_text())
cov=json.loads((root/'coverage.json').read_text())
programs=[(idx,c) for idx,c in enumerate(cases) if c['kind']=='program']
def assembly(c):
    labels={v:k for k,v in c['labels'].items()};out=['.section .text','.globl _start','_start:']
    for idx,ins in enumerate(c['ops']):
        if idx*4 in labels:out.append(labels[idx*4]+':')
        op,*a=ins
        if op in sizes or op=='jalr':s=f'{op} x{a[0]},{a[2]}(x{a[1]})'
        elif op in preds:s=f'{op} x{a[0]},x{a[1]},{a[2]}'
        elif op in rr:s=f'{op} x{a[0]},x{a[1]},x{a[2]}'
        elif op in ii:s=f'{op} x{a[0]},x{a[1]},{a[2]}'
        elif op in ['lui','auipc']:s=f'{op} x{a[0]},0x{a[1]:x}'
        elif op=='jal':s=f'jal x{a[0]},{a[1]}'
        elif op=='fence':s='fence iorw,iorw'
        elif op=='raw':s=f'.word 0x{a[0]:08x}'
        else:s=op
        out.append('    '+s)
    return '\n'.join(out)+'\n'
for idx,c in programs:
    (root/f'programs/{c["name"]}.S').write_text(assembly(c))
    (root/f'programs/{c["name"]}.mem').write_text('\n'.join(f'{w:08x}' for w in c['words']+[0]*(4096-len(c['words'])))+'\n')
note='''# Fault-V：指令驗證與程式級驗收

## ① 驗證用途與系統範圍

本套件使用既有 `fault_v_soc`，包含 CPU、16 KiB 指令記憶體、16 KiB 資料 RAM 與 MMIO 狀態暫存器。工作重點是驗證，不新增或修改 CPU 功能。

| 層級 | 驗證重點 |
| --- | --- |
| 逐指令 | 每個支援名稱都有指定的 target instruction，檢查正常結果或該指令的停止行為 |
| 資料路徑 | signed／unsigned、立即數、位寬、移位、x0、同址讀寫 |
| 控制流程 | PC 更新、Branch 成立／不成立、跳躍、link、對齊 |
| 記憶體 | Load 擴展、Store mask、回應、原始錯誤位址、MMIO 限制 |
| 程式級 | 迴圈、資料相依、Fibonacci、函式／stack、記憶體複製 |
| 重跑 | RAM 保留內容，reset CPU 與 status 後重新執行 |

測試程式使用核心支援的 RV32I 指令名稱與本專案的 ECALL／EBREAK halt 行為。沒有加入標準 machine-mode trap／CSR／中斷，沒有做正式 ISA compliance 認證。

## ② 測試數量與延遲配置

| 類別 | 獨立案例 |
| --- | --- |
| 指定指令的 directed cases | 664 |
| 非法／未支援編碼 | 10 |
| 程式級案例 | 6 |
| 合計 | 680 |

每個案例在兩個真正的 RTL 系統上執行。六個程式在每個模式再重跑一次：`680×2＋6×2＝1372` 次系統執行。

| 模式 | 指令回應延遲 | 資料回應延遲 |
| --- | --- | --- |
| mode 0 | 1 clock | 1 clock |
| mode 1 | 4 clocks | 7 clocks |

延遲是 endpoint 的參數，不是 CPU 的時序驗收。10 ns 的模擬 clock 不代表 FPGA 已能達成 100 MHz。

## ③ 指令覆蓋表

下列數量是每個指令名稱的 focused case 數，不把 setup 指令或程式裡偶然執行的相同指令混入。每個 case 保存 target PC；驗收時確認這個位置真的完成，或依預期產生該指令的對齊／存取／停止事件。

| 指令 | focused cases | 覆蓋重點 |
| --- | --- | --- |
'''
for op,ids in cov.items():
    if op in rr:desc='0、極值、pattern、截斷／比較／移位；rd＝x0／rs1／rs2'
    elif op in ii and op in ['slli','srli','srai']:desc='shamt＝0／1／15／31，正負與極值，x0／讀寫同址'
    elif op in ii:desc='imm＝-2048／-1／0／1／2047，多種運算元與目的暫存器'
    elif op in ['lui','auipc']:desc='upper＝0／1／7FFFF／80000／FFFFF，非零 PC，rd＝x0'
    elif op in preds:desc='成立／不成立、相等、signed／unsigned 極值、未對齊目標'
    elif op=='jal':desc='正／負位移、x0、link、對齊與位移邊界'
    elif op=='jalr':desc='bit 0 清除、負立即數、立即數邊界、rd＝rs1、x0'
    elif op in sizes and op.startswith('l'):desc='合法 lane、符號／零擴展、rd＝base／x0、對齊與存取錯誤'
    elif op in sizes:desc='合法 lane、部分寫入、x0、未對齊與存取錯誤'
    elif op=='fence':desc='Store 已完成後繼續 Load，排序與 PC 正常完成'
    else:desc='先完成 Store，再以獨立原因停止；不產生正常 commit'
    note+=f'| {op.upper()} | {len(ids)} | {desc} |\n'
note+='''
ECALL／EBREAK 的覆蓋由正確的 halt 原因與 target PC 證明，不要求它們正常 retire。其他對齊／存取失敗案例也不應有正常 commit。

R-type 測試包含固定邊界及固定 seed＝20261007 的六組額外運算元；每次生成相同資料。這些是可重現的 operand 樣本，不是無限制 fuzzing。

### 覆蓋率的意思

`names＝40/40` 是 **本規格的指令名稱覆蓋**：每個名稱至少有 focused case 實際被驗收。它不是 RTL line／toggle／branch coverage，也不是所有位元組合、記憶體等待或 fault priority 的全組合證明。

## ④ 邊界值與錯誤規則

| 項目 | 測試重點 |
| --- | --- |
| 加減 | 結果保留低 32-bit，正負極值與溢位截斷 |
| signed 比較 | 0x80000000、0x7FFFFFFF、0xFFFFFFFF，避免減法符號誤判 |
| SLTIU | 立即數先符號擴展，再以 unsigned 比較；包含 -1 |
| R-type 移位 | 只取 rs2[4:0]，包含 0、31、32、63 及高位非零 |
| I-type 移位 | 合法 shamt 0／1／15／31；非法上位功能欄位另測 |
| x0／alias | 寫 x0 忽略；Load x0 仍發交易；rd＝來源時使用更新前資料 |
| Branch | 不成立時忽略未對齊目標；成立時檢查 4-byte 對齊 |
| JALR | 清 bit 0 後仍檢查 bit 1；rd＝rs1 保留舊 base |
| Load／Store | 全部合法 lane、部分 byte 保留、原始 fault_addr |
| byte／halfword 存取失敗 | 對外地址已對齊，但 fault_addr 保留 lane offset |
| MMIO | word-only；窄存取不發請求 |

另有 10 個非法案例：MUL、CSR、FENCE.I、非法 SLLI／JALR／Branch／Load／Store、非精確 ECALL 編碼及全 0 word。這些是非法編碼代表案例，不是枚舉全部 2^32 編碼。

## ⑤ 六個程式與預期結果

| case_id | 程式 | 預期結果 | 每次 commit | 每次資料交易 |
| --- | --- | --- | --- | --- |
'''
results={'fibonacci_12':'F0～F11＝0、1、1、2、3、5、8、13、21、34、55、89',
'loop_sum_100':'x3 與 RAM[0]＝5050','gcd_48_18':'x10 與 RAM[0]＝6',
'nested_call_aligned_stack':'x10 與 RAM[0]＝42；sp 恢復 0x10004000',
'memory_copy_64_checksum':'複製 64 words，checksum＝2016','subword_signed_memory':'擴展正確；最後 word＝0x123400EF'}
for idx,c in programs:note+=f'| {idx} | {c["name"]} | {results[c["name"]]} | {len(c["trace"])} | {len(c["tx"])} |\n'
note+='''
六個程式均以 FENCE、word status＝1 與 EBREAK 結束。Testbench 另外驗證輸出資料與 halt context，沒有只依賴程式自行回報成功。

### RAM 保留內容後重跑

每個程式先執行一次，再 reset CPU／status 後重跑；不清 RAM，不重新注入影像。第二次的預期模型由第一次的最終 RAM 開始，status 從 0 開始。

Store response 回傳的是寫入前舊 word，所以重跑的 response 可能與首次不同；模型保留第二次的預期 raw response，而最終結果與架構 trace 要一致。已接受的 RAM 寫入不因 reset 回滾。

### 完整 Assembly

'''
for idx,c in programs:note+=f'#### {c["name"]}\n\n```asm\n'+assembly(c)+'```\n\n'
note+='''巢狀函式範例分配 16-byte stack frame，先保存 ra，再呼叫內層，返回後恢復 ra／sp。這個測試使用對齊的 stack，但仍不代表完整 C ABI／toolchain 驗證。

`.S` 和 `.mem` 由專案的結構化指令清單產生；機器碼用 Python encoder 編碼，RTL 執行時與指令語意模型比較。這次沒有用 GNU／LLVM assembler，也没有引入 C 程式。六份 `.mem` 各有 4096 words，可用於單獨初始化系統 Top。

## ⑥ Testbench 如何驗證

```text
build_suite.py
    ├→ ISA encoder → 每個案例的機器碼
    └→ 指令語意模型 → trace、交易、register、RAM、halt 預期值
                           │
                           ▼
                        suite.vec
                           │
                           ▼
                   tb_verification_suite
                           │
          reset 時裝入 ROM／準備 RAM fixture
                           │
                           ▼
                  真正 fault_v_soc 執行
                           │
                           ▼
           逐次比對交易／commit，停止時比對完整狀態
```

| 檢查點 | 比對內容 |
| --- | --- |
| 取指 | 每次正常／停止指令一筆取指，不重複執行 |
| 資料 request | 位址、方向、wdata、wstrb |
| 資料 response | raw word、error，每笔恰好一次回應 |
| Commit | InstrPC、指令 word、rd enable／編號／值、下一個 PC |
| 指令未完成 | PC 保持 |
| 交易數 | 全核心最多一筆 outstanding，與模型計數相符 |
| Halt | 原因、fault_pc、原始 fault_addr、PC、status |
| 最終狀態 | 32 個架構暫存器與全部 4096 個資料 RAM words |
| 覆蓋 | 指定 target PC 實際完成或以預期原因停止 |

預期模型以數學運算與 byte array 描述 ISA 行為，不讀 DUT、不模仿 FSM 的 cycle。零值 RAM 用 sparse table 表示，但 testbench 仍比較全部 words。

**每個新案例的初始 ROM／RAM 由 testbench 在 reset 下準備，屬於測試 fixture，不是硬體程式載入介面。**案例執行期間，記憶體 request／response 都由 RTL endpoint 處理；testbench 不修改 CPU register 或替核心完成指令。

## ⑦ 完整 Testbench

'''
note+='```systemverilog\n'+(root/'verify/tb_verification_suite.sv').read_text()+'```\n\n'
note+='''### suite.vec 格式

| 順序 | 資料 |
| --- | --- |
| 檔案第一行 | case 總數 |
| 每個 case header | id、程式旗標、focus id／PC、word／trace／transaction／非零 RAM 數、cause、停止 PC／addr、status |
| program words | 每行一個 32-bit hex word |
| trace | PC、機器碼、rd、value、next PC |
| registers | x0～x31 的 32 行預期值 |
| sparse RAM | word index、value；未列出的預期值為 0 |
| transaction | addr、write、wdata、mask、raw、error、重跑的 raw |

不需手動編輯向量；`python build_suite.py` 可重產生。`suite.json` 保留可閱讀的案例名稱、指令、trace、交易與最後狀態；`coverage.json` 對應每個指令名稱的 case_id。

## ⑧ Vivado 操作與預期輸出

最直接的重現方式：解壓縮後，在檔案包資料夾用 PowerShell 執行 `./run_xsim.ps1`。預設 Vivado 2022.2，可傳入 `-VivadoBin` 調整。

GUI 操作：

1. Design Sources 加入 `rtl` 的 13 個 `.sv`，package 先編譯；只保留一套同名模組。
2. Simulation Sources 加入 `verify/tb_verification_suite.sv`。
3. 將 testbench 的 **VECTOR_FILE** 改成 `suite.vec` 的絕對路徑，使用 `/`。批次腳本的相對路徑是 `../verify/suite.vec`，GUI 工作目錄不一定相同。
4. Simulation Top 選 **tb_verification_suite**，執行 Behavioral Simulation，再 `run all`。
5. 確認兩個 COVERAGE 行與最後 PASS marker，沒有 Fatal。

```text
COVERAGE mode=0 names=40/40 bitmap=ffffffffff runs=686
COVERAGE mode=1 names=40/40 bitmap=ffffffffff runs=686
ALL 1372 ISA AND PROGRAM RUNS PASSED
```

日誌只顯示部分短案例 PASS 與所有程式 PASS；其餘短案例仍逐筆檢查，任何不符合預期的情況會立即 Fatal。兩個延遲模式同時模擬，輸出順序不一定固定。

| 檔案 | 用途 |
| --- | --- |
| rtl | 沿用的完整系統，13 個 RTL 檔案 |
| verify/tb_verification_suite.sv／suite.vec | 驗證環境與向量 |
| programs | 六份 Assembly 與完整記憶體影像 |
| isa_model.py／assembler_support.py | 指令語意與編碼 helper |
| build_suite.py | directed cases、程式與獨立預期值生成 |
| suite.json／coverage.json | 可閱讀案例與指令覆蓋對照 |
| run_xsim.ps1 | 編譯、模擬、PASS 與覆蓋 marker 檢查 |
| logs/verification_results.log | 原始驗證證據 |

## ⑨ 驗收界線

本套件驗收規格中的 40 個指令名稱、代表邊界與錯誤，以及六個程式的功能和 reset 重跑。CPU／系統 RTL 沿用已有版本，沒有因測試數增加而新增硬體功能。

尚未宣稱正式 RISC-V compliance、RTL code coverage、formal proof、完整 C ABI、FPGA 時序／實板或 ASIC sign-off。這些項目需要各自的驗證方式與報告，不能由本套件的 40/40 指令名稱覆蓋替代。
'''
note=note.replace('没有','沒有').replace('每笔','每筆')
(root/'ISA_Program_Verification_Notion.md').write_text(note,encoding='utf-8')
