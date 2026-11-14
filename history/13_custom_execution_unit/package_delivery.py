"""Package only after final RTL and routed FPGA acceptance evidence exists."""
from pathlib import Path
import hashlib,json,re,zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
markers={
 'tb_custom_exec.log':'ALL 16409 CUSTOM UNIT RESULTS PASSED; 11 RESET CANCELLATIONS',
 'tb_custom_cpu.log':'ALL 2638 CUSTOM CPU CASE RUNS PASSED',
 'tb_custom_reset.log':'ALL 7 CUSTOM CPU RESET STAGES PASSED',
 'tb_custom_program.log':'ALL 4 CUSTOM PROGRAM RUNS AND 4 FAULT INJECTIONS PASSED',
 'tb_verification_suite.log':'ALL 1372 ISA AND PROGRAM RUNS PASSED',
 'tb_fault_v_io.log':'ALL 16 IO TRANSACTIONS PASSED',
 'tb_io_faults.log':'ALL 8 CPU IO FAULT CASES PASSED',
 'tb_stress.log':'ALL 4 STRESS PROGRAM RUNS PASSED',
 'tb_payload.log':'ALL 3 PAYLOAD RUNS PASSED; 24 UART BYTES',
}
for name,marker in markers.items():
    text=(ROOT/'logs'/name).read_text(encoding='utf-8-sig')
    assert marker in text and 'Fatal:' not in text,name
build=(ROOT/'logs/final_build.log').read_text(encoding='utf-8-sig')
assert 'CUSTOM FPGA BUILD PASSED' in build
assert 'INTEGRATED DSP COUNT: 1' in build
timing=(ROOT/'logs/timing.rpt').read_text().splitlines()
row=next(timing[i+2].split() for i,line in enumerate(timing) if 'WNS(ns)' in line)
wns,whs,wpws=(float(row[i]) for i in (0,4,8))
assert min(wns,whs,wpws)>=0
assert 'All user specified timing constraints are met.' in '\n'.join(timing)
drc=(ROOT/'logs/drc.rpt').read_text()
warning_counts={}
for line in drc.splitlines():
    if re.match(r'^\|\s*[A-Z][A-Z0-9]*-\d+\s*\|',line):
        fields=[x.strip() for x in line.split('|')]
        assert fields[2]=='Warning',line
        warning_counts[fields[1]]=int(fields[4])
assert warning_counts=={'DPIP-1':2,'DPOP-1':1,'DPOP-2':1},warning_counts
assert int(re.search(r'Violations found:\s+(\d+)',drc).group(1))==4
assert re.search(r'Violations found:\s+0\b',(ROOT/'logs/methodology.rpt').read_text())
route=(ROOT/'logs/route.rpt').read_text()
assert re.search(r'nets with routing errors.*:\s+0\b',route)

util=(ROOT/'logs/utilization.rpt').read_text().splitlines()
def resource(name):
    line=next(line for line in util if line.lstrip().startswith('| '+name))
    return float(line.split('|')[2].strip().replace(',',''))
lut,ff,bram,dsp=map(resource,['Slice LUTs','Slice Registers','Block RAM Tile','DSPs'])
assert dsp==1
hwh=ET.parse(ROOT/'fault_v_custom.hwh')
rx=next(m for m in hwh.iter('MODULE') if m.get('INSTANCE')=='serial_rx')
params={p.get('NAME'):p.get('VALUE') for p in rx.iter('PARAMETER')}
assert params['C_BAUDRATE']=='115200' and params['C_S_AXI_ACLK_FREQ_HZ']=='50000000'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(ROOT/'fault_v_custom.bit')==sha(ROOT/'build/project/fault_v_custom.runs/impl_1/network_wrapper.bit')
assert sha(ROOT/'fault_v_custom.hwh')==sha(ROOT/'build/project/fault_v_custom.gen/sources_1/bd/network/hw_handoff/network.hwh')
report=ROOT/'Verification_Report.md'
section=f'''| 項目 | 最終結果 | 證據 |
| --- | --- | --- |
| 建置 | CUSTOM FPGA BUILD PASSED；整合後 DSP count = 1 | logs/final_build.log |
| Clock 約束 | 50 MHz | logs/timing.rpt |
| Setup／Hold／Pulse width | WNS {wns:.3f} ns、WHS {whs:.3f} ns、WPWS {wpws:.3f} ns；全部指定約束符合 | logs/timing.rpt |
| DRC | 0 Error／Critical Warning；保留 4 個 Warning：DPIP-1×2、DPOP-1、DPOP-2 | logs/drc.rpt |
| Methodology | 0 violations | logs/methodology.rpt |
| Routing | 0 routing errors | logs/route.rpt |
| 資源 | {int(lut)} LUT、{int(ff)} registers、{bram:g} BRAM tiles、{int(dsp)} DSP | logs/utilization.rpt |
| UART IP | 115200 baud 設定、50 MHz AXI clock | fault_v_custom.hwh |

初次合成把單一 product 表達式融合成 DOT4 的乘加 DSP 與 MUL16 的乘法 DSP，共 2 顆，故未採用該版交付。最終使用獨立 fault_v_mul16 階層防止複製，獨立候選合成與整體 routed design 都核對為 1 顆 DSP，且最終 RTL 全部重跑模擬。

PSU-1／PSU-2 negative DDR skew (-0.009／-0.033) 為沿用板上 PYNQ base preset 的保留 critical warnings；沒有修改或豁免這些 board parameters，也未執行 ps7_init。BD 41-702 的 50／50.0 傳播值提示保留。Synth 的未用位元／最佳化、BRAM output register 等提示不等於建置完全無 Warning。若工具產生 vectorless power activity 警告，不以其估計值宣稱實際功耗。

四個 DRC Warning 提示 DSP 的 A／B input、MREG、PREG 未使用內建 pipeline。這版以組合乘法配合外部暫存器達到 50 MHz 約束；保留這些效能／功耗最佳化提示，不改 severity、不宣稱 zero violations。封裝腳本只接受上述明列的四個 Warning，未知規則或其他 severity 會拒絕交付。

資源包含 PS 介接、AXI UART Lite、GPIO 與記憶體；不是單獨 CPU ASIC 面積。不同程式 ROM 內容與平台會影響資源，不能直接把與舊示範版的差值當成純指令擴充成本。'''
s=report.read_text(encoding='utf-8-sig')
s=re.sub(r'(?s)(## FPGA 建置\n\n).*?(\n\n## 實板與效能範圍)',lambda m:m.group(1)+section+m.group(2),s)
s=s.replace('覆盖','覆蓋').replace('与','與')
s=s.split('\n\n## 交付檔案 SHA256',1)[0]
s+='\n\n## 交付檔案 SHA256\n\n'+''.join(f'- {name}：`{sha(ROOT/name)}`\n' for name in ['fault_v_custom.bit','fault_v_custom.hwh','programs/custom_demo.mem','rtl/custom_exec.sv'])
report.write_text(s,encoding='utf-8')
summary={'rtl_simulation':{'markers':markers,'all_passed':True},'fpga':{'clock_mhz':50,'wns_ns':wns,'whs_ns':whs,'wpws_ns':wpws,'lut':int(lut),'registers':int(ff),'bram_tiles':bram,'dsp':int(dsp),'drc_violations':4,'drc_errors_or_critical_warnings':0,'drc_warning_counts':warning_counts,'methodology_violations':0},'physical_board_test':'deferred_by_user','software_vs_custom_benchmark':'not_performed'}
board_record=ROOT/'logs/board_verification.json'
if board_record.exists():
    board=json.loads(board_record.read_text(encoding='utf-8'))
    board_log=(ROOT/'logs/custom_fpga_uart.log').read_text(encoding='utf-8-sig')
    assert 'ALL 3 CUSTOM FPGA UART RUNS PASSED; 24 RECEIVED BYTES' in board_log
    assert 'exit_code=0' in board_log
    assert board['bit_sha256']==sha(ROOT/'fault_v_custom.bit')
    assert board['hwh_sha256']==sha(ROOT/'fault_v_custom.hwh')
    assert board['program_sha256']==sha(ROOT/'programs/custom_demo.mem')
    summary['physical_board_test']='passed_three_uart_and_status_runs'
    summary['board_verification']=board
(ROOT/'validation_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
files=[]
for folder in ['rtl','board','constraints','programs','verify']:
    files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
for name in ['Custom_Execution_Notion.md','Verification_Report.md','README.md','reference.py','assembler_support.py','program_model.py','build_custom.py','generate.py','package_delivery.py','rtl_changes.json','validation_summary.json','run_regression.ps1','run_custom.ps1','run_payload.ps1','run_build.ps1','build.tcl','create_project.tcl','ps_preset.tcl','receive_on_board.py','deploy_and_receive.py','remote_access.py','Fault_V_Custom.ipynb','fault_v_custom.bit','fault_v_custom.hwh','audit/shared_multiplier.tcl']:
    files.append(ROOT/name)
for name in list(markers)+['final_build.log','timing.rpt','drc.rpt','methodology.rpt','route.rpt','utilization.rpt','multiplier_audit.log','candidate_utilization.rpt']:
    files.append(ROOT/'logs'/name)
if board_record.exists():
    files += [board_record,ROOT/'logs/custom_fpga_uart.log',ROOT/'logs/deployed_directory.txt']
manifest={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in files}
(ROOT/'SHA256.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
files.append(ROOT/'SHA256.json')
archive=ROOT/'Fault_V_Custom_CPU.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,str(p.relative_to(ROOT)))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for name,expected in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==expected
print('DELIVERY VALIDATED:',len(files),'files;',archive.stat().st_size,'bytes')
print(json.dumps(summary['fpga']))
