"""Validate actual evidence, derive comparison tables, and package deliverables."""
from pathlib import Path
import csv,hashlib,json,re,zipfile
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return (R/p).read_text(encoding='utf-8-sig')
checks={
 'tb_custom_exec':'ALL 201576 CUSTOM UNIT RESULTS PASSED; 26 RESET CANCELLATIONS; requests=201602 responses=201576',
 'tb_custom_cpu':'ALL 3822 CUSTOM CPU CASE RUNS PASSED',
 'tb_custom_reset':'ALL 52 CUSTOM CPU RESET STAGES PASSED',
 'tb_custom_program':'ALL 4 CUSTOM PROGRAM RUNS AND 4 FAULT INJECTIONS PASSED',
 'tb_verification_suite':'ALL 1372 ISA AND PROGRAM RUNS PASSED',
 'tb_fault_v_io':'ALL 16 IO TRANSACTIONS PASSED',
 'tb_io_faults':'ALL 8 CPU IO FAULT CASES PASSED',
 'tb_stress':'ALL 4 STRESS PROGRAM RUNS PASSED; 4096 UART BYTES PASSED; 4 MID-EXECUTION RESETS PASSED',
 'tb_payload':'ALL 3 PAYLOAD RUNS PASSED; 24 UART BYTES',
 'tb_benchmark':'ALL 112 BENCHMARK RUNS PASSED',
 'tb_unit_comparison':'ALL 16398 SHARED/PARALLEL UNIT COMPARISONS PASSED'}
for top,marker in checks.items():
 log=read('logs/'+top+'.log');assert marker in log and 'Fatal:' not in log,top
assert 'EXTENSION A FPGA BUILD PASSED' in read('logs/final_build.log')
assert 'INTEGRATED DSP COUNT: 4' in read('logs/final_build.log')
assert 'ISOLATED UNIT RESOURCE COMPARISON PASSED' in read('logs/unit_audit.log')

keys=['mode','id','repeat','cycles','instructions','custom','loads','stores','outputs','extra']
pattern=r'BENCH_RESULT mode=(\d+) id=(\d+) repeat=(\d+) cycles=(\d+) instructions=(\d+) custom=(\d+) loads=(\d+) stores=(\d+) outputs=(\d+) extra=(\d+)'
runs=[dict(zip(keys,map(int,m))) for m in re.findall(pattern,read('logs/tb_benchmark.log'))]
assert len(runs)==112
records={(x['mode'],x['id'],x['repeat']):x for x in runs};assert len(records)==112
manifest=json.loads(read('programs/manifest.json'));assert len(manifest)==28
for m in manifest:
 for mode in range(2):
  a=records[mode,m['id'],0];b=records[mode,m['id'],1]
  assert {k:v for k,v in a.items() if k!='repeat'}=={k:v for k,v in b.items() if k!='repeat'}
  for x in [a,b]:
   im,dm=(1,1) if mode==0 else (4,7)
   assert x['cycles']==(im+5)*x['instructions']+(dm+3)*x['loads']+(dm+2)*x['stores']+x['extra']
   assert x['custom']==m['custom_retired'] and x['outputs']==len(m['outputs']) and x['stores']==len(m['outputs'])
 a=records[0,m['id'],0];b=records[1,m['id'],0]
 assert b['cycles']-a['cycles']==3*a['instructions']+6*(a['loads']+a['stores'])

rows=[]
for mode in range(2):
 for i in range(0,28,2):
  a,b=records[mode,i,0],records[mode,i+1,0]
  rows.append(dict(workload=manifest[i]['workload'],memory_mode=mode,rv32i_cycles=a['cycles'],custom_cycles=b['cycles'],rv32i_instructions=a['instructions'],custom_instructions=b['instructions'],rv32i_us_at_50mhz=a['cycles']/50,custom_us_at_50mhz=b['cycles']/50,speedup_at_same_clock=a['cycles']/b['cycles']))
prior=json.loads(read('benchmark_reference/results.json'))
prior_by={(x['memory_mode'],x['workload']):x for x in prior['comparison']}
comparison=[]
for row in rows:
 key=(row['memory_mode'],row['workload'])
 if key in prior_by:
  old=prior_by[key]
  assert row['rv32i_cycles']==old['rv32i_cycles']
  diff=3*(16 if row['workload']=='DOT64' else 32) if row['workload'] in ['DOT64','FIR8_RAW','FIR8_PACKED'] else 0
  assert old['custom_cycles']-row['custom_cycles']==diff
  comparison.append(dict(workload=row['workload'],memory_mode=row['memory_mode'],shared_cycles=old['custom_cycles'],parallel_cycles=row['custom_cycles'],cycles_saved=diff,shared_over_parallel=old['custom_cycles']/row['custom_cycles']))

def util(name):
 s=read(name);out={}
 for key,label in [('lut','Slice LUTs'),('ff','Slice Registers'),('dsp','DSPs'),('bram','Block RAM Tile')]:
  m=re.search(r'\| '+label+r'\*?\s*\|\s*(\d+)',s)
  if m:out[key]=int(m.group(1))
 return out
shared=util('logs/shared_unit_utilization.rpt');parallel=util('logs/parallel_unit_utilization.rpt');platform=util('logs/utilization.rpt')
assert shared['dsp']==1 and parallel['dsp']==4 and platform['dsp']==4
timing=read('logs/timing.rpt');match=re.search(r'WNS\(ns\).*?\n\s*-.*?\n\s*([\d.-]+)\s+[\d.-]+\s+0\s+\d+\s+([\d.-]+)\s+[\d.-]+\s+0\s+\d+\s+([\d.-]+)',timing,re.S)
assert match is not None
wns,whs,wpws=map(float,match.groups());assert min(wns,whs,wpws)>=0
assert 'There are 0 pins that are not constrained for maximum delay.' in timing
drc=read('logs/drc.rpt')
rules=re.findall(r'\| (DP\w+-\d+)\s*\| (\w+)\s*\|[^\n]*?\|\s*(\d+)\s*\|',drc)
assert set((a,b,int(c)) for a,b,c in rules)=={('DPIP-1','Warning',8),('DPOP-1','Warning',4),('DPOP-2','Warning',4)}
assert 'Violations found: 0' in read('logs/methodology.rpt')
assert re.search(r'nets with routing errors[^\n]*:\s*0',read('logs/route.rpt'))
identity=json.loads(read('fpga_identity.json'))
for name,want in identity['sources'].items():assert sha(R/name)==want,name
for name in ['fault_v_extension_a.bit','fault_v_extension_a.hwh']:assert sha(R/name)==identity[name],name
rx=next(m for m in ET.parse(R/'fault_v_extension_a.hwh').iter('MODULE') if m.get('INSTANCE')=='serial_rx')
params={p.get('NAME'):p.get('VALUE') for p in rx.iter('PARAMETER')}
assert params['C_BAUDRATE']=='115200' and params['C_S_AXI_ACLK_FREQ_HZ']=='50000000'
board=json.loads(read('logs/board_verification.json'))
assert board['image_sha256']=={n:identity[n] for n in ['fault_v_extension_a.bit','fault_v_extension_a.hwh']}
assert board['clock_mhz']==50 and len(board['runs'])==3
for x in board['runs']:assert x['uart_hex']=='445350204f4b0d0a' and x['uart_errors']==0 and x['debug']==0x1205

result=dict(measurement='Actual RTL cycle counts; microseconds converted at 50 MHz. Physical FPGA self-check is separate from benchmark timing.',runs=runs,comparison=rows,shared_vs_parallel=comparison,isolated_synthesis=dict(shared=shared,parallel=parallel),routed_platform=platform,timing=dict(clock_mhz=50,wns=wns,whs=whs,wpws=wpws),physical_benchmark_run=False,board_self_check=board)
(R/'results.json').write_text(json.dumps(result,indent=2))
with (R/'results.csv').open('w',newline='',encoding='utf-8-sig') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)

def table(items,fields,labels):
 lines=['| '+' | '.join(labels)+' |','| '+' | '.join(['---']*len(fields))+' |']
 for row in items:lines.append('| '+' | '.join(f'{row[k]:.3f}' if isinstance(row[k],float) else str(row[k]) for k in fields)+' |')
 return '\n'.join(lines)+'\n'
report='''# Fault-V 運算單元擴充：實際驗證報告

實際執行日期：2026-10-14。平台：Vivado／XSim 2022.2、xc7z020clg400-1、PYNQ-Z2。獨立 Notion 筆記只放設計與驗收規則，本文件保存實際證據。

## 驗證範圍

延伸 A 六個方向均有選定實作：四乘法器 DOT4、DOT4ACC／MAC16、ADD8SAT／SUB8SAT、RQNT8、DOT2SAT、DOT8／DOT4SU。保留原四條編碼，共十二條。

| 實際測試 | 結果 | 證據 |
| --- | --- | --- |
| 執行單元 | 201550 個向量＋26 次 reset 後重跑＝201576 個結果正確；接受201602＝完成201576＋取消26 | logs/tb_custom_exec.log |
| packed 飽和 | ADD／SUB 各65536個byte輸入組合；四lane重複同值，另以隨機資料檢查不同lane及carry隔離 | verify/unit.vec |
| 量化 | 21280個特定極值／shift／zero-point組合，另4096隨機向量；Python用divmod，RTL用幅值加偏置捨入 | generate.py、reference.py、rtl/custom_exec.sv |
| CPU | 1911案例×2種記憶體延遲＝3822；每模式1012個非法funct7/funct3組合 | logs/tb_custom_cpu.log |
| CPU reset | 52位置；含額外讀rd、第一／第二拍、回應、提交前；重跑恰好提交一次 | logs/tb_custom_reset.log |
| 完整自我檢查 | 4輪，每輪159個RAM輸出、302次custom、8UARTbytes；2828words ROM | logs/tb_custom_program.log |
| 失敗路徑 | 4次早期／晚期結果破壞，兩種延遲；正確status=2、LED=F及失敗編號 | logs/tb_custom_program.log |
| 原RV32I／程式 | 1372次，兩模式各40/40指令名稱 | logs/tb_verification_suite.log |
| 周邊 | 16 IO交易、8 fault案例 | logs/tb_fault_v_io.log、logs/tb_io_faults.log |
| 壓力 | 4完整程式、4096 UARTbytes、4次RAM/UART執行中reset | logs/tb_stress.log |
| FPGA wrapper | 3輪、24UARTbytes、run與BTN重置 | logs/tb_payload.log |
| benchmark | 28images×2延遲×2reset重跑＝112次；全部輸出正確，重跑cycle相同 | logs/tb_benchmark.log |
| 單獨共用／並行單元 | 原四指令16398向量；數值相同，DOT4 E4／E1，回應持有與一次取走正確 | logs/tb_unit_comparison.log |

所有benchmark都核對FSM公式：cycles=(IMEM_DELAY+5)×retire+(DMEM_DELAY+3)×loads+(DMEM_DELAY+2)×stores+custom_extra。單拍非累加custom額外2拍；累加類或RQNT8／DOT8額外3拍。兩延遲模式的差值另核對3×retire+6×(loads+stores)。

## 50 MHz RTL效能：預設記憶體延遲

'''
report+=table([x for x in rows if x['memory_mode']==0],['workload','rv32i_cycles','custom_cycles','rv32i_instructions','custom_instructions','rv32i_us_at_50mhz','custom_us_at_50mhz','speedup_at_same_clock'],['工作負載','RV32I cycles','Custom cycles','RV32I指令','Custom指令','RV32I μs','Custom μs','加速比'])
report+='\n## 50 MHz RTL效能：較長記憶體延遲\n\n'
report+=table([x for x in rows if x['memory_mode']==1],['workload','rv32i_cycles','custom_cycles','speedup_at_same_clock'],['工作負載','RV32I cycles','Custom cycles','加速比'])
report+='\n## 原相同程式：共用版對並行版\n\n'
report+=table(comparison,['workload','memory_mode','shared_cycles','parallel_cycles','cycles_saved','shared_over_parallel'],['工作負載','延遲模式','共用cycles','並行cycles','省下cycles','共用/並行'])
report+='''
DOT64省48cycles＝16次DOT4×3。兩組FIR8省96cycles＝32次DOT4×3。FIR16／QNT／SATADD的相同程式cycle未改變。原RV32I baseline cycle完全重現。

並行降低單元延遲，仍受取指、Load／Store及FSM影響。RQNT8的軟體benchmark只處理本文件明列的INT32乘積資料；完整48-bit ISA功能由單元與CPU資料驗證。資料初始化／UART不在量測區間；FIR8_RAW打包計入，FIR8_PACKED前處理排除。基準為手寫inline shift/add，不宣稱最佳編譯器結果。

## 資源與時序

'''
report+=table([dict(name='原四指令共用單元（獨立合成）',**shared),dict(name='原四指令並行單元（獨立合成）',**parallel),dict(name='十二指令整合平台（routed）',**platform)],['name','lut','ff','dsp'],['範圍','LUT','FF','DSP'])
report+=f'''
整合平台另使用 {platform['bram']} BRAM tiles；50 MHz WNS={wns} ns、WHS={whs} ns、WPWS={wpws} ns；沒有未約束的內部最大延遲端點，路由錯誤0、Methodology violations0。

DRC保留16個DSP未使用內建pipeline的效能提示：DPIP-1×8、DPOP-1×4、DPOP-2×4；DRC Error／Critical Warning均0，不宣稱zero-warning。BD仍沿用PSU-1／PSU-2負DDR skew(-0.009／-0.033)的PYNQ preset警告，沒有改severity或執行ps7_init；Linux已先SD開機。Power活動推估不能當實測功耗。

獨立四指令單元的資源比較使用相同Vivado合成設定，不包含CPU、IO或RAM，也未為該兩個獨立top做routed timing。並行版省掉lane／累加狀態，故LUT／FF可能下降，DSP由1變4；不可把各種資源混成單一面積數字。

整合平台對原版2760 LUT／2697 FF／8 BRAM／1 DSP增加642 LUT、114 FF、3 DSP；包含八條新增功能及不同ROM，不能全歸因於單獨DOT4並行化。ASIC PPA尚未分析。

## 實板證據

實際上傳並載入本版bit/HWH，ARM讀到50.0 MHz。三輪各8 bytes完全符合DSP OK加CR/LF；錯誤旗標0，FIFO無多餘字元；每輪status=1、halted=1、cause=9。自我檢查每輪核對159個結果。這是功能驗證，benchmark cycle來自RTL模擬；沒有板上cycle counter或功耗量測。

證據：logs/extension_a_fpga_uart.log、logs/board_verification.json、fpga_identity.json。板上結果與本版映像SHA256核對一致。

'''
report+=('使用者確認：LD0／LD2亮，LD1／LD3滅；按住BTN0四燈熄滅，放開後LD0／LD2恢復。此為使用者觀察證據。\n' if board.get('physical_led_observation')=='user_confirmed' and board.get('physical_btn0_observation')=='user_confirmed' else '實體LED／BTN0尚待使用者觀察；RTL wrapper已驗證。\n')
report+='''
## 限制與交付

有限測試不是完整輸入空間形式證明；未驗證外接Pmod電氣傳輸、長時間老化、所有工具鏈、跨製程、ASIC版圖或全框架bit-exact量化。沒有加入延伸B應用、延伸C DMA／流水線或ASIC PPA。CPU仍無標準M/V、CSR／中斷／完整machine-mode。

全部RTL、程式、向量、腳本、映像與實際報告以SHA256清單封裝。Notion技術筆記與本報告分開。重現命令見README.md。
'''
(R/'Verification_Report.md').write_text(report,encoding='utf-8')
summary=dict(test_markers=checks,unit_vectors=201550,unit_results=201576,cpu_runs=3822,cpu_reset_stages=52,benchmark_runs=112,fpga=platform,timing=result['timing'],board=board)
(R/'validation_summary.json').write_text(json.dumps(summary,indent=2))
notes=read('Extension_A_Notion.md')
assert (R/'rtl/custom_exec.sv').read_text() in notes and not re.search(r'Week\s*\d|W\d+|2026-10|DSP／AI CPU 驗證紀錄',notes)
paths=[]
for folder in ['rtl','board','constraints','comparison','programs','verify','logs','benchmark_reference']:
 paths.extend(p for p in (R/folder).rglob('*') if p.is_file() and p.suffix not in ['.jou'])
paths.extend(p for p in R.iterdir() if p.is_file() and p.suffix in ['.py','.ps1','.tcl','.md','.json','.csv','.bit','.hwh'] and p.name not in ['SHA256.json','prepare.py'])
paths.append(R/'known_hosts')
hashes={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in sorted(set(paths))}
(R/'SHA256.json').write_text(json.dumps(hashes,indent=2))
with zipfile.ZipFile(R/'Fault_V_Extension_A.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in hashes:z.write(R/name,name)
 z.write(R/'SHA256.json','SHA256.json')
print('ALL EXTENSION A DELIVERY CHECKS PASSED;',len(hashes)+1,'FILES PACKAGED')
