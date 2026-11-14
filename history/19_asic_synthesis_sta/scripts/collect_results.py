from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1]
L=Path(r"D:\Codex\WSL\fault-v-asic")
out=R/'reports'
rows=[]
tags=['tt_initial','tt_optimized','tt_final','tt_release','tt_sta310','tt_delivery','tt_delivery_reload']
for tag in tags:
 src=L/'design/runs'/tag;dst=out/tag;dst.mkdir(exist_ok=True)
 for rel in ['06-yosys-synthesis/reports','12-openroad-staprepnr','01-openroad-staprepnr','final/metrics.json','final/metrics.csv','resolved.json','config.json','flow.log','warning.log','error.log']:
  a=src/rel;b=dst/rel
  if a.is_dir():shutil.copytree(a,b,dirs_exist_ok=True)
  elif a.is_file():b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
 shutil.copy2(L/'logs'/(tag+'.log'),R/'logs'/(tag+'.log'))
 m=json.loads((src/'final/metrics.json').read_text())
 rows.append({'run':tag,'sta_engine':'3.1.0' if tag in tags[4:] else '2.7.0',**m})
shutil.copytree(L/'design/eco',R/'eco',dirs_exist_ok=True)
shutil.copy2(L/'design/runs/tt_delivery/06-yosys-synthesis/fault_v_asic_top.nl.v',R/'eco/base_mapped.v')
final=L/'design/runs/tt_delivery_reload/final/nl/fault_v_asic_top.nl.v'
assert final.read_bytes()==(R/'mapped_top.v').read_bytes()==(R/'eco/fault_v_asic_top.nl.v').read_bytes()
ident=json.loads((R/'source_identity.json').read_text())
for rel,h in ident.items():
 assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,('local',rel)
 assert hashlib.sha256((L/'design'/rel).read_bytes()).hexdigest()==h,('linux',rel)
for row in rows[-2:]:
 assert row['design__max_slew_violation__count']==row['design__max_cap_violation__count']==0
 assert row['timing__setup__ws']>0 and row['timing__hold__ws']>0
(out/'ppa_comparison.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
(out/'identity_check.json').write_text(json.dumps({'checked_inputs':len(ident),'all_local_and_synthesized_inputs_match':True,'mapped_netlist_sha256':hashlib.sha256(final.read_bytes()).hexdigest(),'accepted_run':'tt_delivery_reload'},indent=2)+'\n',encoding='utf8')
for name in ['opensta_fixed_build.log','cudd_build.log','cudd_source_commit.txt','sta_dependencies.log','sta_fixed_runtime.json']:
 shutil.copy2(L/'logs'/name,R/'logs'/name)
tests=['disable_timing_load_slew','liberty_arcs_one2one_1','liberty_arcs_one2one_2']
t=L/'tools/opensta_fixed/test';d=out/'opensta_upstream';d.mkdir(exist_ok=True)
for name in tests:
 assert (t/'results'/(name+'.log')).read_bytes()==(t/(name+'.ok')).read_bytes(),name
 for rel in [name+'.tcl',name+'.ok','results/'+name+'.log','results/'+name+'.diff']:
  shutil.copy2(t/rel,d/Path(rel).name)
(out/'opensta_upstream_tests.json').write_text(json.dumps({'pass':True,'tests':tests,'scope':'Three targeted Tcl regressions; not the full upstream suite.'},indent=2)+'\n')
print('PASS collected exact sources, serialized netlist, seven runs and three upstream STA tests.')
for x in rows:
 print(x['run'],x['design__instance__area'],x['design__instance__count'],x['timing__setup__ws'],x['timing__hold__ws'],x['design__max_slew_violation__count'],x['design__max_cap_violation__count'])
