"""Verify fresh final-source static IR and every native average-current EM branch."""
from pathlib import Path
import hashlib,json,math
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads((C/p).read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert (C/'logs/final_ir.exit').read_text().strip()=='0'
criteria=read('controls/final_acceptance_criteria.json');inputs=read('reports/final_ir_input.json');core=read('reports/final_core_verified.json');post=read('reports/final_post_verified.json')
assert inputs['ODB_sha256']==core['filled_ODB_sha256']==post['filled_ODB_sha256']
assert inputs['netlist_sha256']==core['fresh_netlist_sha256']==post['fresh_netlist_sha256']
activity=read('functional/final_a/result.json');mixed=next(r for r in activity['activity_runs'] if r['id']=='mixed')
assert mixed['sha256']==inputs['mixed_VCD_sha256']==sha(C/'functional/final_a/mixed/activity.vcd')
em=read('reports/final_em_resistor_audit.json');assert em['native_average_current_screen_pass'] and not em['violations'] and em['temperature_C']==90
cases={};checked_files=0
for budget in ('0p014','0p028'):
    tag='final_ir_'+budget+'_a';run=C/'runs'/tag
    assert (C/'logs'/(tag+'.exit')).read_text().strip()=='0'
    manifest=read('runs/'+tag+'/native_archive_manifest.json');assert manifest['all_byte_exact'] and manifest['canonical_paths_preserved']
    for name,row in manifest['files'].items():
        p=run/name;assert p.resolve().is_relative_to(run.resolve()) and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],str(p)
        checked_files+=1
    step=run/'1-openroad-irdropreport';state=json.loads((step/'state_out.json').read_text());m=state['metrics'];log=(step/'openroad-irdropreport.log').read_text()
    assert 'W25_FINAL_IR_INPUT_HASHES_VERIFIED' in log and 'FAULTV_IR_EM_REVIEW_COMPLETED' in log
    assert m.get('flow__errors__count',0)==0
    drops={}
    for net in ('VPWR','VGND'):
        row=em['cases'][budget][net]
        assert row['source_SHA256']['ODB']==inputs['ODB_sha256'] and row['all_EM_rows_joined_to_exact_native_resistor'] and row['rows']>100000 and row['total_native_resistors']>300000 and not row['violations']
        assert row['source_SHA256']['EM']==sha(step/f'em-{net}.csv') and row['source_SHA256']['resistor_export']==sha(step/f'network-{net}.spice')
        assert all(v['conservative_utilization']<=1 and math.isfinite(v['utilization']) for v in row['worst_per_layer'].values())
        value=m[f'design_powergrid__drop__worst__net:{net}__corner:nom_tt_025C_1v80'];assert math.isfinite(value) and value>=0
        drops[net]=value
    combined=sum(drops.values());assert combined<criteria['static_IR_engineering_budget']['max_combined_VPWR_drop_plus_VGND_rise_V']
    cases[budget]={'worst_rail_drop_V':drops,'conservative_combined_drop_V':combined,'max_average_EM_utilization':max(r['utilization'] for net in em['cases'][budget].values() for r in net['worst_per_layer'].values()),'all_native_EM_branches_pass':True}
record={'final_ODB_sha256':inputs['ODB_sha256'],'final_netlist_sha256':inputs['netlist_sha256'],'mixed_VCD_sha256':mixed['sha256'],'nominal_SPEF_sha256':post['fresh_SPEF_sha256']['nom_*'],'acceptance_criteria_sha256':sha(C/'controls/final_acceptance_criteria.json'),'fresh_archived_files_verified':checked_files,'cases':cases,'research_static_IR_and_average_EM_screen_pass':True,'scope':'Actual common-candidate static average screen under explicit macro loads, ideal core boundary sources, nominal RC and retained four-state activity limitations. The chosen 90mV combined research budget does not qualify nominal Liberty at droop. No package/transient/thermal/crowding/SRAM-interior or complete SPICE sink-load qualification.'}
p=C/'reports/final_ir_verified.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n');print('FINAL_IR_AVERAGE_EM_RESEARCH_SCREEN_VERIFIED',cases,flush=True)
