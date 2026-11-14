from pathlib import Path
import json,re,sys
C=Path(__file__).resolve().parents[1]
stem=sys.argv[1];assert re.fullmatch('antenna_stubs_[a-z]|antenna_restore4|antenna_jumper',stem)
proof=json.loads((C/'reports'/stem/'result.json').read_text())
dr=json.loads((C/'reports'/(stem+'_independent.json')).read_text());cn=json.loads((C/'reports'/(stem+'_all_connectivity.json')).read_text())
assert proof['output_sha256']==dr['odb_sha256']==cn['source_sha256'] and proof['antenna_nets']==dr['unresolved_count']==0 and cn['all_signal_geometry_connected']
state=json.loads((C/'antenna_route_state.json').read_text());state.update(odb='/runtime_final/'+stem+'.odb',metrics={})
cfg=json.loads((C/'config_antenna_route.json').read_text())
for name,value in [('antenna_stub_manual_state.json',state),('config_antenna_stub_manual.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
print('ANTENNA_STUB_CHECKED_EXPORT_READY',proof['output_sha256'],flush=True)
