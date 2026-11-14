"""Promote only after all original routing gates plus covered antenna closure pass."""
from pathlib import Path
import hashlib,json,runpy,sys
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]; assert tag.replace('_','').isalnum()
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'reports'/tag
checks_source=read(out/'checks_source.json')
assert checks_source['run']==tag
for name,digest in checks_source['sha256'].items(): assert sha(R/name)==digest,('Changed actual checker source',name)
launch_path=R/'reports'/f'{tag}_launch.json'; launch=read(launch_path)
assert launch['run']==tag and launch['native_exit']==0
for name,digest in launch['sha256'].items(): assert sha(R/name)==digest,('Changed actual native source',name)
implementations={
    'scripts/antenna_closure_cli.py':'antenna_model_state.json',
    'scripts/antenna_keep_routes_cli.py':'antenna_keep_routes_state.json',
    'scripts/antenna_keep_all_cli.py':'antenna_keep_routes_state.json',
    'scripts/antenna_local_fixed_cli.py':'antenna_local_fixed_state.json',
    'scripts/antenna_resume_cli.py':'antenna_resume_state.json',
}
matched=[p for p in implementations if p in launch['sha256']]
assert len(matched)==1,('Ambiguous or unsupported native implementation',matched)
cli=matched[0];state=implementations[cli]
assert state in launch['sha256']
assert launch.get('cli',cli)==cli and launch.get('state',state)==state
for suffix in ['.exit','_checks.exit']:
    assert (R.parent/'logs'/f'{tag}{suffix}').read_text().strip()=='0'
m=read(R/'runs'/tag/'final/metrics.json')
assert m['route__antenna_violation__count']==m['route__drc_errors']==0
coverage=read(out/'antenna_model_coverage.json'); diodes=read(out/'antenna_diode_checks.json')
route=read(out/'route_checks.json')
assert coverage['pass'] and not coverage['missing_active_input_models'] and diodes['pass']
assert diodes['all_diodes_in_actual_STA_netlist'] and diodes['all_diodes_in_extracted_SPEF'] and diodes['diode_input_capacitance_pf']>0
physical=read(out/'antenna_signal_connectivity.json')
assert physical['pass'] and physical['source_odb_sha256']==diodes['candidate_odb_sha256']
physical_controls=read(R/'reports/antenna_model/signal_gate_controls.json')
assert physical_controls['pass'] and physical_controls['checker_sha256']==sha(R/'scripts/check_antenna_signal_connectivity.py')
assert coverage['source_odb_sha256']==diodes['candidate_odb_sha256']==route['odb_sha256']
assert checks_source['odb_sha256']==route['odb_sha256']
negative=read(R/'reports/antenna_model/negative_coverage.json')
assert negative['pass'] and negative['actual_exit']==1 and negative['no_acceptance_report_created']
assert negative['checker_sha256']==sha(R/'scripts/audit_antenna_metadata.py')
assert read(R/'reports/antenna_model/sram_antenna_model.json')['pass']
# Preserve the preceding accepted scope before writing the stronger new acceptance.
for name in ['accepted_summary.json','handoff_state.json']:
    target=out/('preceding_'+name); assert not target.exists(); target.write_bytes((R/name).read_bytes())
sys.argv=['accept_phase.py','global_desktop_joint_corner',tag]
runpy.run_path(str(R/'scripts/accept_phase.py'),run_name='__main__')
s=read(R/'accepted_summary.json')
assert s['reported_antenna_nets']==0
s.update(antenna_closure=True,antenna_model_coverage=True,antenna_protection_diodes=diodes['passive_diodes'],
         modeled_active_input_pins=coverage['counts']['modeled_active_input_pins'],
         global_overflow_scope='Zero-overflow global parent before antenna repair; final repair geometry separately passes native and independent routing DRC.',
         scope='Week24 core routing acceptance: extracted TT timing/electrical, supported LEF routing DRC and top-level antenna closure with GDS/SPICE-checked SRAM pin metadata. Full foundry DRC/LVS, SRAM internal antenna signoff, multiple PVT and physical signoff remain.')
(R/'accepted_summary.json').write_text(json.dumps(s,indent=2)+'\n')
launch.update(accepted=True,pipeline_exit=0,global_run='global_desktop_joint_corner',cli=cli,config=f'config_{tag}.json',state=state)
launch_path.write_text(json.dumps(launch,indent=2)+'\n')
(R.parent/'logs'/f'{tag}_pipeline.exit').write_text('0\n')
print('ANTENNA CLOSURE AND ALL ORIGINAL ROUTING / RC / TT GATES ACCEPTED')
print(json.dumps(s,indent=2))
