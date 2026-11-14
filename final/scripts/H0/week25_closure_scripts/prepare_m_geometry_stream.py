"""Diagnostic full-GDS check of the branch-only source; antenna is reported separately."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1];read=lambda p:json.loads((C/p).read_text())
proof=read('reports/native_group_m/result.json');dr=read('reports/native_group_m_independent.json');cn=read('reports/native_group_m_all_connectivity.json')
with (C/'inputs/native_group_m.odb').open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
assert digest==proof['output_sha256']==dr['odb_sha256']==cn['source_sha256'] and dr['unresolved_count']==0 and cn['all_signal_geometry_connected'] and cn['checked_multi_terminal_signal_clock_nets']==41337 and not cn['bad_nets'] and not cn['missing_wires']
state=read('runs/antenna_manual_a/1-openroad-detailedrouting/state_out.json');state.update(odb='/runtime_final/native_group_m.odb',metrics={},sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('spef','gds','klayout_gds','def'):state.pop(key,None)
cfg=read('config_working.json');cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','KLayout.StreamOut','KLayout.DRC']};cfg['DECAP_CELLS']=[]
assert cfg['KLAYOUT_CONFLICT_RESOLUTION']=='OverwriteCell'
for name,value in [('native_m_stream_state.json',state),('config_native_m_stream.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
(C/'reports/native_m_geometry_verified.json').write_text(json.dumps({'source_sha256':digest,'independent_native_context_DRC':0,'all_41337_signal_clock_nets_connected':True,'remaining_antenna_nets':proof['antenna_nets'],'accepted_for_final':False,'scope':'Geometry-only eligibility for diagnostic full GDS. Remaining antenna violations are explicit; no final selection or timing/IR/fill acceptance.'},indent=2)+'\n')
print('NATIVE_M_GEOMETRY_VERIFIED_FOR_DIAGNOSTIC_STREAM',digest,proof['antenna_nets'],flush=True)
