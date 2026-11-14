from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
dr=json.loads((C/'reports/signal_gap_independent.json').read_text());cn=json.loads((C/'reports/signal_gap_all_connectivity.json').read_text())
with (C/'inputs/signal_pg_gap.odb').open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
assert digest==dr['odb_sha256']==cn['source_sha256'] and dr['unresolved_count']==0 and cn['all_signal_geometry_connected'] and cn['checked_multi_terminal_signal_clock_nets']==41337
state=json.loads((C/'runs/wide_polish_b/1-openroad-detailedrouting/state_out.json').read_text());state.update(odb='/runtime_final/signal_pg_gap.odb',metrics={})
for key in ('gds','klayout_gds','spef','def'):state.pop(key,None)
cfg=json.loads((C/'config_short_polish.json').read_text());cfg['DRT_THREADS']=2
for name,obj in [('signal_manual_state.json',state),('config_signal_manual.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(obj,indent=2)+'\n')
print('Independently native/context-clean manual source ready for exact export:',digest)
