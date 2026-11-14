from pathlib import Path
import csv,json,re,hashlib,zipfile

ROOT=Path(__file__).resolve().parent
log=(ROOT/'logs/tb_benchmark.log').read_text(encoding='utf-8-sig')
assert 'ALL 48 BENCHMARK RUNS PASSED' in log and 'Fatal:' not in log
pattern=r'BENCH_RESULT mode=(\d+) id=(\d+) repeat=(\d+) cycles=(\d+) instructions=(\d+) custom=(\d+) loads=(\d+) stores=(\d+) outputs=(\d+)'
keys=['mode','id','repeat','cycles','instructions','custom','loads','stores','outputs']
runs=[dict(zip(keys,map(int,m))) for m in re.findall(pattern,log)]
assert len(runs)==48
manifest=json.loads((ROOT/'programs/manifest.json').read_text())
by_id={m['id']:m for m in manifest}
records={}
for run in runs:
    key=(run['mode'],run['id'],run['repeat']);assert key not in records;records[key]=run
    m=by_id[run['id']]
    assert run['custom']==m['custom_retired'] and run['outputs']==len(m['outputs'])
    imem,dmem=(1,1) if run['mode']==0 else (4,7)
    extra=5 if m['workload'] in ['DOT64','FIR8_RAW','FIR8_PACKED'] else 2
    formula=(imem+5)*run['instructions']+(dmem+3)*run['loads']+(dmem+2)*run['stores']+extra*run['custom']
    assert run['cycles']==formula,(m,run,formula)
for mode in range(2):
    for id in range(12):
        a,b=records[(mode,id,0)],records[(mode,id,1)]
        assert {k:v for k,v in a.items() if k!='repeat'}=={k:v for k,v in b.items() if k!='repeat'}
for id in range(12):
    a,b=records[(0,id,0)],records[(1,id,0)]
    assert b['cycles']-a['cycles']==3*a['instructions']+6*(a['loads']+a['stores'])

# Bind the tested RTL snapshot to the source of the previously verified FPGA.
rtl_sha={}
source_manifest=json.loads((ROOT/'hardware_reference/source_manifest.json').read_text())
for p in (ROOT/'rtl').glob('*.sv'):
    digest=hashlib.sha256(p.read_bytes()).hexdigest()
    assert digest==source_manifest['rtl/'+p.name]
    rtl_sha[p.name]=digest
(ROOT/'rtl_sha256.json').write_text(json.dumps(rtl_sha,indent=2),encoding='utf-8')

# Recompute dataset goldens with direct integer arithmetic, not the software routine.
v=json.loads((ROOT/'programs/benchmark_vectors.json').read_text())
assert sum(a*b for a,b in zip(v['dot64']['a'],v['dot64']['b']))==v['dot64']['expected']
for key in ['fir8','fir16']:
    assert [sum(v[key]['samples'][n+k]*v[key]['coefficients'][k] for k in range(8)) for n in range(16)]==v[key]['expected']
assert [min(127,max(-128,x//8)) for x in v['fir8']['expected']]==v['fir8']['quantized']
assert [min(2147483647,max(-2147483648,a+b))&0xffffffff for a,b in zip(v['satadd64']['a'],v['satadd64']['b'])]==v['satadd64']['expected_u32']

rows=[]
for mode in range(2):
    for id in range(0,12,2):
        base=records[(mode,id,0)];custom=records[(mode,id+1,0)]
        rows.append({'workload':by_id[id]['workload'],'memory_mode':mode,'clock_mhz_reference':50,
         'rv32i_cycles':base['cycles'],'custom_cycles':custom['cycles'],
         'rv32i_instructions':base['instructions'],'custom_instructions':custom['instructions'],
         'rv32i_loads':base['loads'],'custom_loads':custom['loads'],
         'stores_each':base['stores'],'custom_retired':custom['custom'],
         'rv32i_us_at_50mhz':base['cycles']/50,'custom_us_at_50mhz':custom['cycles']/50,
         'speedup_at_same_clock':base['cycles']/custom['cycles'],
         'correct_outputs':True,'repeated_counts_identical':True})
(ROOT/'results.json').write_text(json.dumps({'measurement':'RTL cycle counts; time converted at reference 50 MHz, not physical benchmark timing','runs':runs,'comparison':rows,'cycle_formula_checks':48,'physical_benchmark_run':False},indent=2),encoding='utf-8')
with (ROOT/'results.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def table(mode):
    header='| 工作負載 | RV32I cycles | Custom cycles | RV32I 指令數 | Custom 指令數 | RV32I μs | Custom μs | 加速比 |\n| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |\n'
    return header+''.join(f"| {r['workload']} | {r['rv32i_cycles']:,} | {r['custom_cycles']:,} | {r['rv32i_instructions']:,} | {r['custom_instructions']:,} | {r['rv32i_us_at_50mhz']:.2f} | {r['custom_us_at_50mhz']:.2f} | {r['speedup_at_same_clock']:.2f}× |\n" for r in rows if r['memory_mode']==mode)

notes='''# Fault-V：RV32I 與 DSP／AI 自訂指令效能比較

## 1．比較目的與範圍

使用相同的多周期 Fault-V 核心、相同資料與記憶體配置，比較純 RV32I 軟體運算與四條自訂指令。兩種程式都在同一個具備自訂單元的 CPU RTL 上執行；RV32I 版完全不使用自訂指令或標準 M 的乘除法。

Cycle 與退休指令數由 XSim 中的實際 RTL 執行量測。時間以 50 MHz 換算，50 MHz 取自相同核心既有 FPGA 平台的時序與實板 clock 驗證；不是把本次 benchmark 放到 Z2 上的秒錶或硬體計數器量測。

## 2．工作負載

| 名稱 | 定義 | 比較範圍 |
| --- | --- | --- |
| DOT64 | 兩組 64 個 signed INT8 內積；答案 60256 | 同一份連續 byte 陣列；RV32I 每對 LB＋軟體乘法，custom 每四對 LW＋DOT4 |
| FIR8_RAW | signed INT8 八抽頭 FIR，23 個輸入、16 個 INT32 輸出 | 原始 byte 資料；custom 的 LBU／移位／OR 視窗打包也計入 |
| FIR8_PACKED | 相同 FIR 運算，輸入視窗預先打包為兩個對齊 word | 僅 kernel；兩版讀相同預打包資料，排除產生視窗的前處理成本 |
| FIR16 | signed INT16 八抽頭 FIR、16 個 INT32 輸出 | 相同 halfword 陣列；MUL16 對比軟體乘法 |
| QNT16 | 對 16 個 FIR8 結果算術右移 3，再限制到 INT8 範圍 | 同樣從 INT32 陣列讀取，寫入符號擴展 INT32 結果 |
| SATADD64 | 64 對 signed INT32 的飽和加法 | 同一份陣列，包含一般加法與正／負溢位 |

FIR 定義為 y[n] = sum(x[n+k] × h[k])，k=0～7，n=0～15。完整資料在 programs/benchmark_vectors.json；記憶體初始化在 programs/inputs.mem。

FIR 的係數在量測區間內載入一次，八個 tap 在程式中展開，外層輸出迴圈仍於 CPU 執行。兩版都避免每個輸出重新從 RAM 載入所有係數。

## 3．RV32I 軟體基準

| 功能 | 軟體實作 |
| --- | --- |
| Signed 乘法 | 先判斷符號、對 INT8／INT16 來源取絕對值，以 shift-and-add 計算，乘數為 0 時提早結束，再恢復符號 |
| 飽和加法 | 一般 ADD，再以 XOR／signed branch 判斷溢位，選 INT32 上下限 |
| INT8 量化 | SRA、兩個界限比較與必要的限制值寫入 |
| 函式呼叫成本 | 以上運算 inline 展開，不額外加入 JAL／JALR 呼叫與返回開銷 |

這是可讀、可重現的手寫基準，不宣稱是最佳化到極限的 RV32I 實作。Signed 乘法的 early-exit 路徑和加減／限制分支會受資料影響，因此加速比是這份資料與這個實作的結果，不是指令的固定通用加速倍數。

## 4．量測邊界

1. 資料在 testbench 載入 RAM，reset 與此步驟不計入。
2. 第一個 PC=0 的取指請求被接受的 cycle 開始計數，包含 kernel 的指標、係數與迴圈初始化。
3. 完成最後一條 kernel 指令的 cycle 仍計入。
4. 下一次取指到 kernel_end 標記時停止，該次取指與標記指令不計入。
5. 之後的成功狀態寫入、EBREAK 與所有 testbench 比對排除。

Kernel 的載入、輸出 Store、分支、資料打包與 custom 等待全部計入。程式不輸出 UART，避免串列通訊時間影響比較。量測不需要 CPU 支援標準 cycle／instret CSR。

每個程式都核對完整輸出陣列、custom 提交次數、輸出 Store 次數及正常 EBREAK；每個配置重置後執行兩次，cycle、退休指令與資料交易數應完全一致。

## 5．記憶體配置

| 模式 | IMEM RESPONSE_DELAY | DMEM RESPONSE_DELAY | 用途 |
| --- | ---: | ---: | --- |
| 0 | 1 | 1 | 目前 SoC 基準參數 |
| 1 | 4 | 7 | 檢查等待較長時的收益與量測一致性 |

參數不等於一次完整存取的 CPU cycle 數，還有 request／response 與 FSM 階段。兩版在同一模式比較，不跨模式直接計算加速比。

## 6．模式 0 的結果

下表的時間都是 cycle / 50 MHz 換算值。

'''+table(0)+'''
## 7．模式 1 的結果

'''+table(1)+'''
## 8．如何解讀

- DOT64 和 FIR16 的收益較大，因為一條乘法／內積指令取代多個位元迴圈與分支。
- FIR8_RAW 包含 CPU 實際打包成本，比 FIR8_PACKED 更接近從原始資料開始的 kernel 使用情境。
- 模式 0 下，custom FIR8_RAW 為 4046 cycles，預打包版為 1550 cycles；減少的 2496 cycles 不代表前處理免費，而是打包移到量測範圍外。
- RV32I 的預打包 FIR 需要移位擷取 signed lane，雖然少讀 RAM，仍可能比直接 LB 稍慢；不能把 RAW／PACKED 當成相同端到端成本。
- QNT8 與 ADDSAT 的收益較小：本來的 RV32I 序列較短，Load／Store、迴圈與自訂握手占比較高。
- 記憶體等待增加後，加速比會改變。不能只以 DOT4 的四個 lane 推論一定四倍，也不能把 FPGA 軟體跑測試的秒數當成 CPU 執行時間。

## 9．公式與一致性檢查

```text
execution_time = cycles / clock_frequency
speedup = baseline_time / custom_time
同頻率時：speedup = rv32i_cycles / custom_cycles
```

依目前 FSM，基礎 ALU／Branch／Jump 的每次執行為 IMEM_DELAY+5 cycles；Load 再加 DMEM_DELAY+3，Store 再加 DMEM_DELAY+2。DOT4 比基礎指令再多 5 cycles，其餘三種 custom 多 2 cycles。

```text
C = (IMEM_DELAY+5)*退休指令數
  + (DMEM_DELAY+3)*Load 交易數
  + (DMEM_DELAY+2)*Store 交易數
  + custom 額外執行週期
```

這個公式用來獨立核對計數器邊界，不用來替代 RTL 量測。兩模式的差值還必須符合：

```text
C_mode1 - C_mode0 = 3*退休指令數 + 6*(Loads+Stores)
```

## 10．頻率與硬體資源

| 項目 | 相同核心既有 FPGA 平台的參考值 |
| --- | --- |
| 板卡／時脈 | PYNQ-Z2，50 MHz |
| LUT／Registers | 2760／2697 |
| BRAM／DSP | 8 BRAM tiles／1 DSP |
| Setup／Hold slack | WNS 7.756 ns／WHS 0.064 ns |
| ROM 映像 | 前一階段的 DSP 自我檢查程式，不是本次 12 個 benchmark 映像 |

兩種程式使用相同具備 custom unit 的 RTL，因此本次沒有比較「拆掉 custom unit 的較小 CPU」與「擴充 CPU」的硬體成本。上表是已有綜合／實板證據的參考平台，不是兩種新程式映像各自重新綜合後的資源結果；ROM 內容与重新佈線可能影響資源與時序。

hardware_reference/ 保留該平台的報告與實板 clock 證據。ASIC 面積、頻率與功耗需要指定製程後另行分析，不能由 FPGA LUT／DSP 數直接代換。

## 11．檔案與執行

在 outputs/benchmark 資料夾執行：

```powershell
python .\\build_benchmarks.py
powershell -ExecutionPolicy Bypass -File .\\run_benchmark.ps1
python .\\make_results.py
```

| 檔案 | 用途 |
| --- | --- |
| rtl/ | 與已驗證自訂 CPU 相同的 16 個 RTL 檔 |
| programs/*.S／*.mem | 六個工作負載、各兩種版本的 Assembly 與機器碼 |
| programs/inputs.mem | 所有測試共用的原始資料／預打包資料 |
| programs/manifest.json | 量測結束位址、預期 custom 數與完整輸出 |
| verify/tb_benchmark.sv | Cycle／retire／資料交易量測與功能檢查 |
| logs/tb_benchmark.log | 原始 RTL 量測輸出 |
| results.csv／results.json | 完整數值、重複測量與比較資料 |
| hardware_reference/ | 前一平台的頻率、資源與實板證據，與 benchmark 量測分開 |
| Verification_Report.md | 實際驗證紀錄與限制 |

本套腳本不重新下載 FPGA。本次結果是 RTL cycle benchmark；若要新增實板效能量測，需要能讀到量測計數的硬體介面，並載入對應 benchmark 映像。

## 12．後續延伸的選擇

先以這份數據作為共用乘法器版本的基準，再比較四乘法器並行 DOT4。也應優先處理 FIR 視窗的資料排列與打包，而不是只增加運算單元。每項延伸都需保留相同資料、量測邊界、完整答案與硬體成本，才能判斷收益来自指令、資料搬移或前處理。
'''
notes=notes.replace('与','與').replace('来自','來自')
(ROOT/'Benchmark_Notion.md').write_text(notes,encoding='utf-8')
report='''# Benchmark 驗收紀錄

日期：2026-10-14（Asia/Taipei），Vivado / XSim 2022.2。

| 驗收 | 結果 |
| --- | --- |
| 程式 | 六工作負載 × RV32I／custom = 12 個映像，均在 4096-word ROM 範圍內 |
| RTL 執行 | 12 映像 × 2 記憶體模式 × 2 次重複 = 48 次，全數通過 |
| 正確性 | 每個輸出 word 對固定 golden 比對，status=1、HALT_EBREAK |
| 重複性 | 每配置兩次 cycle、retire、custom、Load、Store 數相同 |
| 基準合法性 | 所有基準 binary 靜態排除 custom-0 與 M；動態 custom retire=0；kernel 禁止 M |
| 計數邊界 | fetch 數=retire 數、exact output store 數；48 筆均符合獨立 FSM cycle 公式 |
| 記憶體差值 | 12 映像均符合 Δcycles=3*instructions+6*(loads+stores) |
| 核心來源 | 16 個 RTL SHA256 與 custom_core/rtl 相同；沒有修改硬體 |

證據：logs/tb_benchmark.log、results.json、rtl_sha256.json。

```text
ALL 48 BENCHMARK RUNS PASSED; OUTPUTS AND REPEATED COUNTS VERIFIED
```

Cycle 是 RTL 執行量測，μs 為 50 MHz 換算。50 MHz 的物理時脈與資源來自已驗證的 DSP 自我檢查 overlay，保存在 hardware_reference/；本次沒有新建 bitstream、沒有把 12 個 benchmark 映像載入 Z2、沒有實板 performance counter 結果。

基準與 custom 執行在相同擴充核心，不是 RV32I-only 小核心與 custom 核心的 PPA 比較。本次資源參考值未因不同 ROM 重新綜合，所以不填入不存在的各版本硬體資源差值。

FIR8_PACKED 排除預打包成本；FIR8_RAW 計入 CPU 視窗打包，但不包含資料從外部主機進入 RAM 的時間。兩者都屬此處明確定義的 kernel 範圍，不能用 PACKED 加速比宣稱完整系統端到端效能。

Early-exit 軟體乘法與條件分支依賴輸入資料。結果不代表最佳 RV32I 編譯器輸出、不代表其他資料集、Cache／Pipeline 核心或所有 clock／memory 配置；未量測 ASIC 功耗與面積。
'''
(ROOT/'Verification_Report.md').write_text(report,encoding='utf-8')
files=[]
for folder in ['rtl','programs','verify','hardware_reference']:
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
for name in ['Benchmark_Notion.md','Verification_Report.md','README.md','build_benchmarks.py','make_results.py','run_benchmark.ps1','assembler_support.py','program_model.py','reference.py','results.csv','results.json','rtl_sha256.json','logs/tb_benchmark.log']:
    files.append(ROOT/name)
sha={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
(ROOT/'SHA256.json').write_text(json.dumps(sha,indent=2),encoding='utf-8');files.append(ROOT/'SHA256.json')
with zipfile.ZipFile(ROOT/'Fault_V_Benchmark.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,str(p.relative_to(ROOT)))
with zipfile.ZipFile(ROOT/'Fault_V_Benchmark.zip') as z:
    assert z.testzip() is None
    for name,digest in sha.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest
print('ALL 48 RTL MEASUREMENTS AND CYCLE FORMULA CHECKS VERIFIED')
for row in rows:
    if row['memory_mode']==0:print(row['workload'],row['rv32i_cycles'],row['custom_cycles'],round(row['speedup_at_same_clock'],3))
print('Packaged',len(files),'files')
