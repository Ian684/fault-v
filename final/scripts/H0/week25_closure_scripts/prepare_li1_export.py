from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads((C/p).read_text())
proof=read('reports/li1_spacing/result.json');dr=read('reports/li1_spacing_independent.json');cn=read('reports/li1_spacing_all_connectivity.json')
assert proof['output_sha256']==dr['odb_sha256']==cn['source_sha256'] and proof['antenna_nets']==dr['unresolved_count']==0 and cn['all_signal_geometry_connected']
assert read('reports/li1_rule_replay_verified.json')['fixed_li1_and_li3_markers']==0
state=read('runs/antenna_manual_a/1-openroad-detailedrouting/state_out.json');state.update(odb='/runtime_final/li1_spacing.odb',metrics={})
for key in ('spef','def','gds','klayout_gds'):state.pop(key,None)
cfg=read('config_antenna_stub_manual.json')
for name,value in [('li1_manual_state.json',state),('config_li1_manual.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
print('LI1_VERIFIED_EXPORT_PREPARED',proof['output_sha256'],flush=True)
