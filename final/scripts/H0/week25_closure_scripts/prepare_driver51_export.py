from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
proof=json.loads((C/'reports/driver51_trial_b.json').read_text());dr=json.loads((C/'reports/driver51_independent.json').read_text());cn=json.loads((C/'reports/driver51_all_connectivity.json').read_text())
with (C/'inputs/driver51_b.odb').open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
assert digest==proof['output_sha256']==dr['odb_sha256']==cn['source_sha256'] and dr['unresolved_count']==0 and cn['all_signal_geometry_connected']
state=json.loads((C/'runs/signal_manual_a/1-openroad-detailedrouting/state_out.json').read_text());state.update(odb='/runtime_final/driver51_b.odb',metrics={})
for key in ('spef','gds','klayout_gds','def'):state.pop(key,None)
p=C/'driver51_manual_state.json';assert not p.exists();p.write_text(json.dumps(state,indent=2)+'\n')
p=C/'scripts/driver51_export_cli.py';assert not p.exists();p.write_text((C/'scripts/signal_manual_export_cli.py').read_text().replace('signal_pg_gap.odb','driver51_b.odb'))
print('DRIVER51_CHECKED_EXPORT_INPUT',digest)
