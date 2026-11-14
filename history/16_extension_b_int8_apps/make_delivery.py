from pathlib import Path
import csv,hashlib,json,re,zipfile
import xml.etree.ElementTree as ET
from application_models import outputs,input_image
from binary_model import run
R=Path(__file__).resolve().parent
def read(name):return (R/name).read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads(read('baseline_identity.json'))
assert len(baseline['rtl'])==16
for name,want in baseline['rtl'].items():assert sha(R/'rtl'/name)==want,('CPU changed',name)
markers={
 'tb_custom_exec':'ALL 201576 CUSTOM UNIT RESULTS PASSED; 26 RESET CANCELLATIONS',
 'tb_verification_suite':'ALL 1372 ISA AND PROGRAM RUNS PASSED',
 'tb_fault_v_io':'ALL 16 IO TRANSACTIONS PASSED',
 'tb_io_faults':'ALL 8 CPU IO FAULT CASES PASSED',
 'tb_stress':'ALL 4 STRESS PROGRAM RUNS PASSED; 4096 UART BYTES PASSED; 4 MID-EXECUTION RESETS PASSED',
 'tb_applications':'ALL 408 APPLICATION RUNS PASSED; 136 MID-EXECUTION RESETS',
 'tb_application_demo':'ALL 4 APPLICATION DEMO RUNS AND 4 FAULT INJECTIONS PASSED',
 'tb_payload':'ALL 3 PAYLOAD RUNS PASSED; 24 UART BYTES'}
for top,marker in markers.items():
 text=read('logs/'+top+'.log');assert marker in text and 'Fatal:' not in text,top
manifest=json.loads(read('programs/application_manifest.json'));data=json.loads(read('programs/application_datasets.json'))
quality=json.loads(read('programs/quality.json'));assert len(manifest)==68 and len(data)==34
keys=['mode','id','repeat','cycles','instructions','custom','loads','stores','outputs','extra']
pattern=r'APP_RESULT mode=(\d+) id=(\d+) repeat=(\d+) cycles=(\d+) instructions=(\d+) custom=(\d+) loads=(\d+) stores=(\d+) outputs=(\d+) extra=(\d+)'
runs=[dict(zip(keys,map(int,m))) for m in re.findall(pattern,read('logs/tb_applications.log'))]
records={(x['mode'],x['id'],x['repeat']):x for x in runs};assert len(runs)==len(records)==408

# Recompute mathematical answers and interpret each exact delivered machine image.
for m in manifest:
 d=data[m['dataset']];gold,q=outputs(d);assert gold==[tuple(v) for v in m['outputs']]
 encoded=[int(x,16) for x in read('programs/applications/'+m['image']).splitlines()]
 initial=input_image(d)
 loaded=[int(x,16) for x in read('programs/applications/'+m['inputs']).splitlines()]
 assert b''.join(x.to_bytes(4,'little') for x in loaded)==initial
 result=run(encoded,initial,m['end_pc']);assert result['counts']==m['counts'] and result['status']==1
 for i,want in gold:assert int.from_bytes(result['ram'][i*4:i*4+4],'little')==want
 if m['variant']=='rv32i':assert all((w&127)!=11 and not ((w&127)==0x33 and w>>25==1) for w in encoded)
 for mode in range(2):
  first=records[mode,m['id'],0]
  for rep in range(3):
   x=records[mode,m['id'],rep]
   assert {k:v for k,v in first.items() if k!='repeat'}=={k:v for k,v in x.items() if k!='repeat'}
   for name in ['instructions','custom','loads','stores','extra']:assert x[name]==m['counts'][name]
   assert x['outputs']==len(gold)
   im,dm=(1,1) if mode==0 else (4,7)
   assert x['cycles']==(im+5)*x['instructions']+(dm+3)*x['loads']+(dm+2)*x['stores']+x['extra']
 a,b=records[0,m['id'],0],records[1,m['id'],0]
 assert b['cycles']-a['cycles']==3*a['instructions']+6*(a['loads']+a['stores'])

rows=[]
for mode in range(2):
 for i in range(0,68,2):
  a,b=records[mode,i,0],records[mode,i+1,0];m=manifest[i]
  rows.append(dict(app=m['app'],case=m['case'],memory_mode=mode,rv32i_cycles=a['cycles'],custom_cycles=b['cycles'],rv32i_instructions=a['instructions'],custom_instructions=b['instructions'],rv32i_loads=a['loads'],custom_loads=b['loads'],stores_each=a['stores'],custom_retired=b['custom'],rv32i_us_at_50mhz=a['cycles']/50,custom_us_at_50mhz=b['cycles']/50,speedup_at_same_clock=a['cycles']/b['cycles']))
aggregate=[]
for mode in range(2):
 for app in dict.fromkeys(d['app'] for d in data):
  selected=[x for x in rows if x['app']==app and x['memory_mode']==mode]
  aggregate.append(dict(app=app,memory_mode=mode,datasets=len(selected),sum_rv32i_cycles=sum(x['rv32i_cycles'] for x in selected),sum_custom_cycles=sum(x['custom_cycles'] for x in selected),weighted_speedup=sum(x['rv32i_cycles'] for x in selected)/sum(x['custom_cycles'] for x in selected),minimum_speedup=min(x['speedup_at_same_clock'] for x in selected),maximum_speedup=max(x['speedup_at_same_clock'] for x in selected)))

build=read('logs/final_build.log');assert 'EXTENSION B FPGA BUILD PASSED' in build and 'INTEGRATED DSP COUNT: 4' in build
timing=read('logs/timing.rpt')
m=re.search(r'WNS\(ns\).*?\n\s*-.*?\n\s*([\d.-]+)\s+[\d.-]+\s+0\s+\d+\s+([\d.-]+)\s+[\d.-]+\s+0\s+\d+\s+([\d.-]+)',timing,re.S);assert m
wns,whs,wpws=map(float,m.groups());assert min(wns,whs,wpws)>=0
assert 'There are 0 pins that are not constrained for maximum delay.' in timing
util=read('logs/utilization.rpt');resources={}
for key,label in [('lut','Slice LUTs'),('ff','Slice Registers'),('dsp','DSPs'),('bram','Block RAM Tile')]:resources[key]=int(re.search(r'\| '+label+r'\*?\s*\|\s*(\d+)',util).group(1))
assert resources['dsp']==4
rules=re.findall(r'\| (DP\w+-\d+)\s*\| (\w+)\s*\|[^\n]*?\|\s*(\d+)\s*\|',read('logs/drc.rpt'))
assert set((a,b,int(c)) for a,b,c in rules)=={('DPIP-1','Warning',8),('DPOP-1','Warning',4),('DPOP-2','Warning',4)}
assert 'Violations found: 0' in read('logs/methodology.rpt')
assert re.search(r'nets with routing errors[^\n]*:\s*0',read('logs/route.rpt'))
identity=json.loads(read('fpga_identity.json'))
for name,want in identity['sources'].items():assert sha(R/name)==want,name
images=['fault_v_extension_b.bit','fault_v_extension_b.hwh']
for name in images:assert sha(R/name)==identity[name]
rx=next(m for m in ET.parse(R/'fault_v_extension_b.hwh').iter('MODULE') if m.get('INSTANCE')=='serial_rx')
params={p.get('NAME'):p.get('VALUE') for p in rx.iter('PARAMETER')};assert params['C_BAUDRATE']=='115200' and params['C_S_AXI_ACLK_FREQ_HZ']=='50000000'
board=json.loads(read('logs/board_verification.json'))
assert board['image_sha256']=={n:identity[n] for n in images}
assert board['clock_mhz']==50 and len(board['runs'])==3
for x in board['runs']:assert x['uart_hex']=='415050204f4b0d0a' and x['uart_errors']==0 and x['debug']==0x1205

summary=dict(measurement='Actual RTL cycles; times converted at 50 MHz; physical functional self-check separate from benchmark timing',runs=runs,comparison=rows,aggregate=aggregate,quality=quality,resources=resources,timing=dict(clock_mhz=50,wns=wns,whs=whs,wpws=wpws),board=board,physical_benchmark_run=False,rtl_changed=False,optimizations_deferred_until_abc_complete=True)
(R/'results.json').write_text(json.dumps(summary,indent=2))
with (R/'results.csv').open('w',newline='',encoding='utf-8-sig') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
quality_rows=[dict(app=q['app'],case=q['case'],max_abs_error_lsb=q['max_abs_error_lsb'],saturation_count=q.get('saturation_count',0)) for q in quality if 'max_abs_error_lsb' in q]
with (R/'quality.csv').open('w',newline='',encoding='utf-8-sig') as f:
 writer=csv.DictWriter(f,fieldnames=list(quality_rows[0]));writer.writeheader();writer.writerows(quality_rows)
def table(items,fields,labels):
 lines=['| '+' | '.join(labels)+' |','| '+' | '.join(['---']*len(fields))+' |']
 for row in items:lines.append('| '+' | '.join(f'{row[k]:.4f}' if isinstance(row[k],float) else str(row[k]) for k in fields)+' |')
 return '\n'.join(lines)+'\n'
report='''# Fault-V 應用擴充：實際驗證報告

實際執行日期：2026-10-14；Vivado／XSim 2022.2、xc7z020clg400-1、PYNQ-Z2。依原流程完成應用階段；優化、創意及新問題研究留到A／B／C完成後。

## 完成範圍與設計身分

INT8 Conv1D、24→4全連接層、Conv→量化／ReLU→FC→量化／argmax串接，另有Q15 FIR8、IIR1、FFT16。16個CPU／SoC RTL檔案全部SHA256與已驗證XFaultVDSP v1.1基準一致；更換的是應用ROM與平台wrapper的ROM檔名。

卷積6乘積視窗使用DOT4ACC，FC用六組DOT4ACC，量化RQNT8；FIR/IIR用MAC16；FFT複數乘法使用四次MUL16。未新增ISA、DMA、scratchpad或pipeline。

## 實際功能驗證

| 項目 | 結果 | 證據 |
| --- | --- | --- |
| 直接參考 | 34資料集；卷積／FC／串接各6、FIR5、IIR4、FFT7 | application_models.py、programs/application_datasets.json |
| 機器碼模型 | 68個RV32I／custom image全部輸出正確；實際指令、Load、Store、custom數用於RTL交叉檢查 | binary_model.py、programs/application_manifest.json |
| RTL完整應用 | 68images×2延遲×3重跑＝408次；所有INT32、packed INT8、argmax、Q15／複數輸出正確，來源資料不改動 | logs/tb_applications.log |
| 中途reset | 每image／延遲模式1次，共136次；pending RAM交易中reset，保留RAM再跑，結果與cycle一致 | logs/tb_applications.log |
| 示範ROM | 4輪；每輪132項結果、548次custom、8UARTbytes；2359words，未超過4096word IMEM | logs/tb_application_demo.log |
| 失敗路徑 | 4次；兩模式各早期／FFT晚期破壞，失敗編號1／101，status=2、GPIO=F、EBREAK | logs/tb_application_demo.log |
| FPGA wrapper | 3輪、24UARTbytes，run與BTN reset通過 | logs/tb_payload.log |
| 原自訂單元 | 201576個結果、26次取消；握手與數值回歸通過 | logs/tb_custom_exec.log |
| 原RV32I／程式 | 1372次，兩模式各40/40指令名稱 | logs/tb_verification_suite.log |
| 原IO／fault | 16交易、8錯誤案例 | logs/tb_fault_v_io.log、logs/tb_io_faults.log |
| 原stress | 4完整程式、4096UARTbytes、4次RAM/UART執行中reset | logs/tb_stress.log |

三次完整執行包含兩次重新載入RAM及一次中斷後保留RAM重啟。每次動態指令／交易數都與獨立機器碼模型一致。Cycle逐筆核對：(IMEM_DELAY+5)×instructions＋(DMEM_DELAY+3)×loads＋(DMEM_DELAY+2)×stores＋custom_extra。兩延遲模式差值另核對3×instructions＋6×(loads+stores)。

第一輪遇到的是測試平台逾時誤報：較快模式完成後仍計時，等待較慢模式時超過每程式限制。修正done gating後全部重跑通過。FC named輸入也補正為實際零／正／負／交錯極值資料；展示ROM的內容SHA保持不變。第一輪log留存供追溯，不作成功證據。

## 效能：所有資料集加總比較

下表每個資料集只取一次完整執行，不把重跑當新樣本。加總RV32I cycles／加總custom cycles是加權加速比，不是各加速比的平均；每組詳細資料另在results.csv。

'''
report+=table(aggregate,['app','memory_mode','datasets','sum_rv32i_cycles','sum_custom_cycles','weighted_speedup','minimum_speedup','maximum_speedup'],['應用','延遲模式','資料集','RV32I總cycles','Custom總cycles','加權加速比','最小','最大'])
report+='\n## 個別資料集：預設延遲模式\n\n'
report+=table([x for x in rows if x['memory_mode']==0],['app','case','rv32i_cycles','custom_cycles','rv32i_instructions','custom_instructions','speedup_at_same_clock'],['應用','資料','RV32I cycles','Custom cycles','RV32I指令','Custom指令','加速比'])
report+='''
Cycle來自RTL；μs按50MHz換算。包含指標／迴圈初始化、原始輸入Load、卷積CPU打包、bias、量化／ReLU、argmax、串接資料搬移、FFT bit-reversal／twiddle／工作RAM及所有單元等待；排除testbench資料載入、reset、完成回報、EBREAK、UART。兩種程式都在相同擴充CPU上執行，RV32I版本不含custom/M；不是不同面積CPU的比較。

RV32I使用可提早結束的inline signed shift/add，不宣稱最佳編譯器實作。量化資料限定比例乘積可放INT32；完整RQNT8指令48-bit語意沿用基準。加速依資料與控制路徑而異。

## 固定點精度與飽和

LSB是原始Q15整數單位，實數誤差等於下列值／32768。FIR對已限制INT16的理想浮點結果比較；IIR對無逐步取整的浮點回授；FFT對直接O(N²)正向DFT／16。

'''
report+=table(quality_rows,['app','case','max_abs_error_lsb','saturation_count'],['應用','資料','最大誤差LSB','限制次數'])
report+='''
非飽和FFT六案例最大誤差4LSB，檢查門檻12LSB；IIR最大約2.3501LSB，門檻4LSB；FIR非飽和誤差小於1LSB。Full-scale FFT案例有3個stage/component限制，對未限制浮點DFT的誤差約8416.34LSB，屬已知飽和失真；整數RTL符合逐階段限制的golden，不宣稱此案例有低失真精度。

圖表：figures/DSP_Precision.png與.pdf。Twiddle +1量化為32767，每階段算術右移1，最後比例1/16；逐階段取整不能等同於最後一次取整。

## FPGA與實板

'''
report+=f"整合平台：{resources['lut']} LUT、{resources['ff']} FF、{resources['bram']} BRAM tiles、{resources['dsp']} DSP。50 MHz WNS={wns} ns、WHS={whs} ns、WPWS={wpws} ns；無未約束內部最大延遲端點，route errors=0、Methodology violations=0。\n\n"
report+='''DRC Error／Critical Warning=0，保留16個DSP pipeline效能建議：DPIP-1×8、DPOP-1×4、DPOP-2×4。PYNQ PS preset沿用PSU-1／PSU-2負DDR skew(-0.009／-0.033) critical warnings，沒有改severity、修改這些參數或執行ps7_init；板子先SD開機Linux。不宣稱所有建置訊息無warning，也不把vectorless power推估當實測功耗。

實際載入配對bit/HWH，ARM讀到50.0MHz，三次每次8bytes完全符合APP OK＋CR/LF，errors=0、FIFO無多餘字元、status=1、halted=1、cause=9。每輪CPU自行比較132項結果。板上資料與fpga_identity的映像SHA一致，證據為logs/extension_b_fpga_uart.log、logs/board_verification.json。

'''
report+=('使用者確認：LD0／LD2亮、LD1／LD3滅；按住BTN0四燈熄滅，放開後LD0／LD2恢復。這是使用者觀察證據。\n' if board.get('physical_led_observation')=='user_confirmed' and board.get('physical_btn0_observation')=='user_confirmed' else '實體LED／BTN0尚待使用者觀察；wrapper模擬已通過。\n')
report+='''
## 範圍限制與交付

未量測板上benchmark cycle、實際功耗或外部Pmod電氣傳輸；未做訓練／真實資料集分類準確率、所有模型尺寸、所有係數、完整輸入空間形式證明、DMA／pipeline／ASIC PPA。有限案例的精度不保證任意資料同樣表現。

卷積kernel定義為不反轉權重的sum input[n+k,c]×weight[o,k,c]。FIR有效視窗對應一般filter的反向係數及n+7對齊。IIR定義正回授係數0.75。參考：[SciPy差分方程](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html)、[FFT forward normalization](https://docs.scipy.org/doc/scipy/reference/generated/scipy.fft.fft.html)。逐步固定點政策以本專案規格為準。

Notion只放架構、演算法、資料格式、介面、操作與驗收規則；本報告、CSV、logs、figure與SHA256交付包保留實際證據。按照使用者安排，下一階段沿原路線做C，優化、創意與新問題研究暫緩。
'''
(R/'Verification_Report.md').write_text(report,encoding='utf-8')
(R/'validation_summary.json').write_text(json.dumps(dict(test_markers=markers,application_images=68,application_datasets=34,rtl_runs=408,mid_execution_resets=136,rom_words=2359,board_checks=132,resources=resources,timing=summary['timing'],board=board,rtl_changed=False),indent=2))
notes=read('Application_Extensions_Notion.md');assert not re.search(r'Week\s*\d|W\d+|2026-10|實際驗證報告',notes)
paths=[]
for folder in ['rtl','board','constraints','figures','reference_reports']:
 paths.extend(p for p in (R/folder).rglob('*') if p.is_file())
paths.extend((R/'programs/applications').glob('*'))
for p in (R/'programs').iterdir():
 if p.is_file() and (p.name.startswith('application') or p.name.startswith('io_') or p.name.startswith('stress') or p.name=='quality.json'):paths.append(p)
active_verify=['tb_custom_exec.sv','unit.vec','tb_verification_suite.sv','suite.vec','tb_fault_v_io.sv','tb_io_faults.sv','tb_stress.sv','tb_applications.sv','applications.vec','tb_application_demo.sv','application_demo_outputs.vec','tb_payload.sv']
paths.extend(R/'verify'/name for name in active_verify)
paths.extend(p for p in (R/'logs').iterdir() if p.is_file() and p.suffix in ['.log','.rpt','.json','.txt'])
paths.extend(p for p in R.iterdir() if p.is_file() and p.suffix in ['.py','.ps1','.tcl','.md','.json','.csv','.bit','.hwh'] and p.name!='SHA256.json')
paths.append(R/'known_hosts')
hashes={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in sorted(set(paths))}
(R/'SHA256.json').write_text(json.dumps(hashes,indent=2))
with zipfile.ZipFile(R/'Fault_V_Extension_B.zip','w',zipfile.ZIP_DEFLATED) as z:
 for name in hashes:z.write(R/name,name)
 z.write(R/'SHA256.json','SHA256.json')
print('ALL EXTENSION B DELIVERY CHECKS PASSED;',len(hashes)+1,'FILES PACKAGED')
for x in aggregate:
 if x['memory_mode']==0:print(x['app'],round(x['weighted_speedup'],3))
