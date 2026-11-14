"""Use the common final ODB, extracted RC and actual final-netlist workload activity."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads((C/p).read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert (C/'logs/final_functional.exit').read_text().strip()=='0'
activity=read('functional/final_a/result.json');targets=read('functional/final_a/activity_targets.json')
assert activity['all_reset_CDC_and_four_workloads_pass']
stage=read('reports/runtime_final_filled_odb.json');assert targets['candidate_ODB_sha256']==stage['sha256']
vcd=C/'functional/final_a/mixed/activity.vcd'
mixed=next(row for row in activity['activity_runs'] if row['id']=='mixed');assert sha(vcd)==mixed['sha256']
assert read('reports/runtime_final_mixed_vcd.json')['sha256']==mixed['sha256']
state=read('runs/focus_post_b/5-openroad-rcx/state_out.json')
assert state['nl'].endswith('/focus_post_b/1-openroad-fillinsertion/fault_v_asic_top.nl.v')
assert sha(C/Path(state['nl']).relative_to('/work/week25_closure'))==activity['netlist_sha256']
state.update(odb='/runtime/final_filled.odb',spef={'nom_*':state['spef']['nom_*']},metrics={},sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('gds','klayout_gds'):state.pop(key,None)
cfg=read('config_pg_ir.json');cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc'
for name,value in [('final_ir_state.json',state),('config_final_ir.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
code=(C/'controls/pg_ir_native.tcl').read_text().replace('/runtime/mixed.activity.vcd','/runtime/final_mixed.vcd')
spef=Path(state['spef']['nom_*']);spef_sha=sha(C/spef.relative_to('/work/week25_closure'))
guards='\n'.join(f'if {{[lindex [exec sha256sum {path}] 0] ne "{digest}"}} {{error "Final IR input hash mismatch: {key}"}}' for key,path,digest in [('ODB','$::env(CURRENT_ODB)',stage['sha256']),('SPEF','$::env(CURRENT_SPEF_DEFAULT_CORNER)',spef_sha),('VCD','/runtime/final_mixed.vcd',mixed['sha256'])])+'\n'
code=code.replace('read_current_odb\n','read_current_odb\n'+guards+'puts "W25_FINAL_IR_INPUT_HASHES_VERIFIED"\n')
out=C/'controls/final_ir_native.tcl';assert not out.exists();out.write_text(code)
code=(C/'scripts/pg_ir_native_cli.py').read_text().replace('/controls/pg_ir_native.tcl','/controls/final_ir_native.tcl')
out=C/'scripts/final_ir_cli.py';assert not out.exists();out.write_text(code)
(C/'reports/final_ir_input.json').write_text(json.dumps({'ODB_sha256':stage['sha256'],'netlist_sha256':activity['netlist_sha256'],'mixed_VCD_sha256':mixed['sha256'],'SPEF':state['spef'],'macro_budgets_W_each':[0.014,0.028],'scope':'Final common-candidate activity + TT nominal RC with explicit macro load assumptions; no package/thermal/SRAM-internal or AC/pulsed EM qualification.'},indent=2)+'\n')
print('FINAL_IR_FRESH_INPUTS_BOUND',stage['sha256'],flush=True)
