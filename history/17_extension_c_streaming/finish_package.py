"""Build the reviewable report and archive from successful, source-bound evidence."""
from pathlib import Path
import json,re,hashlib,zipfile,sys
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def resource(text,label):
 match=re.search(r'^\|\s*'+re.escape(label)+r'\s*\|\s*(\d+)\s*\|',text,re.M)
 assert match,label
 return int(match[1])
def finish():
 sim=json.loads((R/'simulation_validation.json').read_text());identity=json.loads((R/'fpga_identity.json').read_text())
 for name,digest in identity['sources'].items():assert sha(R/name)==digest,name
 for name in ['fault_v_extension_c.bit','fault_v_extension_c.hwh']:assert sha(R/name)==identity[name]
 timing=(R/'logs/timing.rpt').read_text();table=timing.split('WNS(ns)',1)[1].splitlines()[2].split()
 wns,whs,wpws=float(table[0]),float(table[4]),float(table[8]);assert min(wns,whs,wpws)>=0
 util=(R/'logs/utilization.rpt').read_text();resources={k:resource(util,label) for k,label in [('lut','Slice LUTs'),('ff','Slice Registers'),('bram','Block RAM Tile'),('dsp','DSPs')]};assert resources['dsp']==8 and resources['bram']==9
 drc=(R/'logs/drc.rpt').read_text();warnings={}
 for rule,severity,count in re.findall(r'^\|\s*([\w-]+)\s*\|\s*(Warning|Error|Critical Warning)\s*\|[^|]+\|\s*(\d+)\s*\|',drc,re.M):
  assert severity=='Warning',(rule,severity);warnings[rule]=int(count)
 methodology=(R/'logs/methodology.rpt').read_text();assert 'Violations found: 0' in methodology
 route=(R/'logs/route.rpt').read_text();assert re.search(r'# of fully routed nets[.\s]*:\s*\d+',route,re.I), 'route report missing'
 assert re.search(r'# of nets with routing errors[.\s]*:\s*0\s*:',route,re.I),'routing errors'
 build=(R/'logs/final_build.log').read_text(encoding='utf-8-sig');assert 'EXTENSION C FPGA BUILD PASSED' in build
 critical=sorted(set(re.findall(r'CRITICAL WARNING: \[([^\]]+)\]',build)))
 board=json.loads((R/'logs/board_verification.json').read_text());assert len(board['runs'])==3
 assert board['image_sha256']=={n:identity[n] for n in ['fault_v_extension_c.bit','fault_v_extension_c.hwh']}
 assert abs(board['clock_mhz']-50)<.01
 for run in board['runs']:assert run['uart_hex']=='43204f4b0d0a' and run['uart_errors']==0 and run['debug']==0x1205
 data=dict(simulation=sim,resources=resources,timing=dict(clock_mhz=50,wns=wns,whs=whs,wpws=wpws),drc_warnings=warnings,methodology_violations=0,build_critical_warning_codes=critical,board=board,image_identity=identity)
 (R/'validation.json').write_text(json.dumps(data,indent=2))
 useful={r['mode']:r for r in sim['concurrent_rows'] if r['repeat']==0}
 lines=['# Fault-V 延伸 C：驗證與效能報告','',
 '本報告記錄實際驗證證據；設計筆記另見 `Streaming_Architecture_Notion.md`。CPU 維持多周期及十二條自訂指令，新增 4 KiB scratchpad、word-copy DMA、獨立三階段 DOT4 向量加速器與三來源記憶體仲裁器。','',
 '## 模擬驗收','',
 '| 項目 | 實際結果 |','| --- | --- |',
 '| DOT4 pipeline | 33,280 筆結果；全速與隨機背壓；4 次 reset flush；無背壓 II＝1、握手延遲＝3 clocks |',
 '| 仲裁器 | 6,000 筆交易；CPU／DMA／ACC 各 2,000；請求／回應保持、錯誤路由、reset 取消 |',
 '| SoC 整合 | 124 情境 × 2 記憶體延遲模式 × 3 次＝744 次；92 次執行中 reset 後以保留 RAM 重啟 |',
 '| 故障與限制 | 長度、對齊、範圍、位址 wrap、buffer overlap、引擎衝突、CPU lock、busy 設定寫入、只讀／窄寫、DMA／ACC 讀寫錯誤及 tag 錯誤 |',
 '| C 示範程式 | 137 項自檢；4 次正常執行及4次結果破壞；失敗編號65／134正確，成功UART為 C OK + CR/LF |',
 '| Z2 wrapper | 3 次正常執行、18 UART bytes；ARM run 控制、BTN0 reset、LED與debug訊號 |',
 '| 既有自訂運算單元 | 201,576 筆結果、26 次 reset 取消 |',
 '| ISA／程式回歸 | 1,372 次 |',
 '| 周邊／CPU周邊錯誤 | 16 筆周邊交易、8 個 CPU fault 情境 |',
 '| Stress | 4 次程式執行、4,096 UART bytes、4 次中途 reset |',
 '| 原本六種應用 | 408 次、136 次中途 reset；原本二進位指令數、交易數及 cycle 公式仍符合；另4次展示及4次故障注入 |','',
 '最終測試 log 的驗收標記全部存在且無 Fatal。Golden outputs 以 Python 整數運算產生；C 的非同步 DMA／ACC 沒有假借只支援原本 CPU 的 binary model 驗證。舊應用仍使用原有獨立 binary model。','',
 '同時工作情境：DMA 搬 256 words、ACC 計算64組DOT4、CPU執行200次獨立加一。快模式有%d clocks兩引擎同時busy，其中%d次有用CPU加一在引擎busy時完成；慢模式分別為%d clocks與%d次。DMA512筆記憶體交易、ACC129筆、CPU2筆，結果全部正確。'%(useful[0]['concurrent_cycles'],useful[0]['cpu_useful'],useful[1]['concurrent_cycles'],useful[1]['cpu_useful']),'',
 '## 效能量測','',
 '量測來源是 RTL simulation 的 clock 計数。比較同一SoC、相同輸入、相同50 MHz與相同記憶體延遲；包含整個程式的設定、啟動、輪詢、CPU loop、完成狀態寫入及停止成本。測試前由testbench裝載資料，不將該裝載時間算入程式；表中的CHAIN則把CPU或DMA搬移本身算入。','',
 '**DOT／CHAIN 的 CPU 基準已使用 DOT4ACC 自訂指令**；不是純RV32I乘法軟體。COPY的CPU基準使用LW／SW。硬體版本的控制成本完全算入，沒有宣稱所有資料量都加速。','',
 '| 工作 | N | 快模式CPU cycles | 快模式引擎 cycles | 加速比 | 慢模式CPU cycles | 慢模式引擎 cycles | 加速比 |','| --- | --- | --- | --- | --- | --- | --- | --- |']
 for kind,label in [('COPY_main_sp','主RAM→scratchpad搬移'),('DOT_main','DOT4向量點積'),('CHAIN','搬移後點積')]:
  for n in [1,4,16,64,256,1024]:
   values=[next(b for b in sim['benchmarks'] if b['kind']==kind and b['n']==n and b['mode']==g) for g in [0,1]];a,b=values
   lines.append('| %s | %d | %d | %d | %.3f× | %d | %d | %.3f× |'%(label,n,a['cpu_cycles'],a['engine_cycles'],a['speedup'],b['cpu_cycles'],b['engine_cycles'],b['speedup']))
 lines += ['',
 '快模式IMEM／資料RAM回應延遲為1／1 clocks；慢模式為4／7 clocks。共84組比較，另涵蓋scratchpad→主RAM、主RAM→主RAM及scratchpad輸入DOT4。三次重跑的cycle數一致，詳見 `stream_benchmarks.csv` 及 `logs/stream_mode*.csv`。','',
 '![RTL效能比較](figures/Streaming_Performance.png)','',
 '三階段運算pipeline的II＝1不等於整機每拍一組DOT4；串行讀取A／B及共用記憶體仲裁是整機吞吐量限制。本測試未量測實體板上的benchmark counter、功耗或最高可用頻率。','',
 '## FPGA建置與成本','',
 '| 項目 | 延伸B平台 | 延伸C平台 |','| --- | --- | --- |',
 '| LUT | 3402 | %d |'%resources['lut'],
 '| FF | 2811 | %d |'%resources['ff'],
 '| DSP | 4 | %d |'%resources['dsp'],
 '| BRAM tiles | 8 | %d |'%resources['bram'],
 '| Clock | 50 MHz | 50 MHz |',
 '| Setup WNS | 3.738 ns | %.3f ns |'%wns,
 '| Hold WHS | 0.030 ns | %.3f ns |'%whs,
 '| Pulse-width WPWS | 9.020 ns | %.3f ns |'%wpws,'',
 'C多出一個scratchpad及四個加速器乘法器；上述資源是整個Z2平台，包括PS7與AXI周邊。Setup／Hold與pulse width均無負slack，methodology violations為0。','',
 '最終DRC無Error或Critical Warning，保留%d個Warning：%s。DSP警告是DPIP／DPOP內部暫存器建議；運算pipeline使用外部暫存器，不代表DSP內建AREG／MREG／PREG已啟用。'%(sum(warnings.values()),', '.join('%s×%d'%x for x in warnings.items())),'',
 'Vivado建置的Critical Warning代碼：%s。既有Z2 PS preset保留PSU-1／PSU-2的負DDR skew（−0.009／−0.033）；不執行ps7_init重設ARM DDR。這些不是Fault-V資料路徑的DRC失敗，仍保留在建置證據中。'%(', '.join(critical) or '無'),'',
 'LED與UART外部輸出沒有同步接收clock，約束使用false path；switch只對同步器第一級使用false path。因此此時序驗收不等於外部Pmod UART接線的電氣驗證。','',
 '## 實板與映像身分','',
 'PYNQ-Z2透過SSH／Ethernet載入最終映像，ARM讀取PL AXI UARTLite。三次均收到 `43 20 4F 4B 0D 0A`（C OK + CR/LF），總計18 bytes、UART error＝0、FCLK0＝50 MHz、debug＝0x1205（status1、halted、EBREAK原因9）。','',
 '使用者LED／BTN0觀察：'+('已確認LD0／LD2亮，按住BTN0四燈熄滅，放開恢復。' if board.get('physical_led_observation') and board.get('physical_btn0_observation') else '待使用者確認；上述UART／debug為已完成的實板讀回證據。'),'',
 'Bitstream SHA-256：`%s`'%identity['fault_v_extension_c.bit'],
 'HWH SHA-256：`%s`'%identity['fault_v_extension_c.hwh'],'',
 '`fpga_identity.json`將映像與RTL、board wrapper、約束、ROM及Tcl綁定；`logs/build_sources_started.json`與建置完成來源相同。早期建置不列入交付驗收；曾在建置途中改ROM的版本由來源快照檢查拒絕。','',
 '## 限制與已修正問題','',
 '- 只提供word-copy DMA、單一工作描述與一筆仲裁後未完成交易；沒有descriptor ring、scatter/gather、中斷、cache coherency或AXI burst。',
 '- CPU與引擎、兩引擎間的buffer所有權規則保守，來源只讀也鎖定；違規CPU存取直接停止。',
 '- 已接受的記憶體寫入不保證在bus error／reset時回復。寫回錯誤案例刻意驗證RAM可能已變動而PROGRESS尚未增加。',
 '- 發現並修正tag錯誤停止時可能留下已發出讀取的情形：先排空該response，再釋放BUSY及仲裁器，禁止結果寫入。',
 '- 修正testbench的posedge驅動競態、XSim動態檔名字串、force/release殘值；示範程式修正UART ready輪詢；後期結果破壞測試等待新DMA工作的BUSY後再等待DONE，避免誤用上次sticky DONE。早期失敗log保留供追查。',
 '- CPU／ISA相關15個原本RTL檔逐byte不變；原有檔案只有`fault_v_soc.sv`修改，新增6個RTL檔。',
 '- FPGA功能、時序與資源驗收不等於ASIC sign-off；ASIC SRAM、標準元件、DFT、STA corners、DRC／LVS及交付規則仍屬後續工作。','',
 '重現入口與環境見README；完整原始碼、testbench、fixtures、腳本、bit／hwh及報告包含於ZIP。']
 (R/'Verification_Report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 files=[]
 for folder in ['rtl','board','constraints','verify','programs','logs','reference_reports','figures']:
  files.extend(p for p in (R/folder).rglob('*') if p.is_file() and p.suffix not in ['.wdb','.pb','.rpx','.str'])
 files.extend(p for p in R.iterdir() if p.is_file() and p.suffix in ['.py','.ps1','.tcl','.md','.json','.csv','.bit','.hwh'] and p.name!='package_manifest.json')
 files.append(R/'known_hosts')
 manifest={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in sorted(set(files))}
 (R/'package_manifest.json').write_text(json.dumps(dict(file_count=len(manifest),sha256=manifest),indent=2));files.append(R/'package_manifest.json')
 archive=R/'Fault_V_Extension_C.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(set(files)):z.write(p,p.relative_to(R).as_posix())
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None
  for name,digest in manifest.items():assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
  assert len(z.namelist())==len(manifest)+1
 print('Packaged and CRC/SHA-256 checked',len(manifest)+1,'files:',archive.name)
if __name__=='__main__':finish()
