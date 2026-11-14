"""Prepare export only after exact-source DRC/connectivity/antenna gates."""
from pathlib import Path
import json,re,sys
C=Path(__file__).resolve().parents[1];stem,tag=sys.argv[1:]
assert re.fullmatch(r'native_(?:upper_[a-z]|group_[a-z])',stem) and re.fullmatch('[a-z0-9_]+',tag)
read=lambda p:json.loads((C/p).read_text())
proof=read('reports/'+stem+'/result.json');dr=read('reports/'+stem+'_independent.json');cn=read('reports/'+stem+'_all_connectivity.json')
assert proof['output_sha256']==dr['odb_sha256']==cn['source_sha256'] and proof['antenna_nets']==dr['unresolved_count']==0 and cn['all_signal_geometry_connected']
assert cn['checked_multi_terminal_signal_clock_nets']==41337 and not cn['missing_wires'] and not cn['bad_nets']
state=read('runs/antenna_manual_a/1-openroad-detailedrouting/state_out.json');state.update(odb='/runtime_final/'+stem+'.odb',metrics={})
for key in ('spef','def','gds','klayout_gds'):state.pop(key,None)
cfg=read('config_antenna_stub_manual.json')
for name,value in [(tag+'_state.json',state),('config_'+tag+'.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
print('NATIVE_VERIFIED_EXPORT_PREPARED',stem,proof['output_sha256'],flush=True)
