"""Acceptance evidence and measured end-to-end RTL timings."""
from pathlib import Path
import csv,json,hashlib,re,statistics
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def analyze():
 rows=[]
 for g in [0,1]:
  with (R/'logs'/('stream_mode%d.csv'%g)).open() as f:
   for row in csv.DictReader(f):rows.append({k:v if k=='name' else int(v) for k,v in row.items()})
 assert len(rows)==744 and len({(x['mode'],x['id'],x['repeat']) for x in rows})==744
 assert len(json.loads((R/'programs/stream_manifest.json').read_text()))==124
 bench=[]
 for g in [0,1]:
  grouped={}
  for row in rows:
   if row['mode']!=g or row['id']>=84:continue
   parts=row['name'].split('_');n=int(parts[-1])
   if parts[0]=='CHAIN':kind='CHAIN';engine='_'.join(parts[1:-1])
   else:kind='_'.join(parts[:-2]);engine=parts[-2]
   grouped.setdefault((kind,n),{}).setdefault(engine,[]).append(row)
  for (kind,n),engines in grouped.items():
   cpu=engines['CPU'];hw=next(v for k,v in engines.items() if k!='CPU')
   assert len(cpu)==3 and len(hw)==3
   assert len({x['cycles'] for x in cpu})==1 and len({x['cycles'] for x in hw})==1
   c=cpu[0]['cycles'];h=hw[0]['cycles'];bench.append(dict(mode=g,imem_delay=1 if g==0 else 4,dmem_delay=1 if g==0 else 7,kind=kind,n=n,cpu_cycles=c,engine_cycles=h,speedup=c/h,cpu_us=c/50,engine_us=h/50))
 with (R/'stream_benchmarks.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(bench[0]));w.writeheader();w.writerows(bench)
 markers={'tb_dot_pipeline':'ALL 33280 PIPELINE RESULTS PASSED; 4 RESET FLUSHES; II=1 LATENCY=3','tb_mem_arbiter':'ALL 6000 ARBITER TRANSACTIONS PASSED','tb_streams':'ALL STREAM SCENARIO RUNS PASSED','tb_stream_demo':'ALL 4 STREAM DEMO RUNS AND 4 INJECTED SELF-CHECK FAILURES PASSED','tb_payload':'ALL 3 PAYLOAD RUNS PASSED; 18 UART BYTES','tb_custom_exec':'ALL 201576 CUSTOM UNIT RESULTS PASSED','tb_verification_suite':'ALL 1372 ISA AND PROGRAM RUNS PASSED','tb_fault_v_io':'ALL 16 IO TRANSACTIONS PASSED','tb_io_faults':'ALL 8 CPU IO FAULT CASES PASSED','tb_stress':'ALL 4 STRESS PROGRAM RUNS PASSED','tb_applications':'ALL 408 APPLICATION RUNS PASSED','tb_application_demo':'ALL 4 APPLICATION DEMO RUNS AND 4 FAULT INJECTIONS PASSED'}
 for top,marker in markers.items():
  log=(R/'logs'/(top+'.log')).read_text(encoding='utf-8-sig');assert marker in log and 'Fatal:' not in log,top
 log=(R/'logs/tb_streams.log').read_text();assert all('STREAM MODE %d COMPLETE runs=372 resets=46'%g in log for g in [0,1])
 baseline=json.loads((R/'baseline_identity.json').read_text());source=baseline.get('rtl',baseline.get('sources',baseline))
 # Baseline has an explicit files mapping; insist on unchanged CPU/ISA source.
 source=baseline.get('files',source)
 same=[];changed=[]
 for path,digest in source.items():
  if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):continue
  p=R/path
  if not p.exists():p=R/'rtl'/path
  (same if sha(p)==digest else changed).append(str(p.relative_to(R)).replace('\\','/'))
 assert len(same)==15 and changed==['rtl/fault_v_soc.sv'],(same,changed)
 data=dict(test_markers=markers,stream_scenarios=124,stream_runs=744,stream_midexecution_resets=92,pipeline_results=33280,arbiter_transactions=6000,benchmark_pairs=84,benchmarks=bench,concurrent_rows=[x for x in rows if x['name']=='CONCURRENT'],baseline_rtl_unchanged=same,baseline_rtl_changed=changed,demonstration=json.loads((R/'programs/stream_demo.json').read_text()))
 (R/'simulation_validation.json').write_text(json.dumps(data,indent=2))
 print('Validated 744 stream runs, 84 comparison pairs, all legacy application and wrapper markers, and 15 unchanged baseline RTL files.')
if __name__=='__main__':analyze()
