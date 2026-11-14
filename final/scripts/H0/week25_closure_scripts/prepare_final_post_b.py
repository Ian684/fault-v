"""Start final export/extraction only from a fully checked signal+PG+antenna route."""
from pathlib import Path
import json,re
C=Path(__file__).resolve().parents[1];selection=json.loads((C/'reports/final_route_selection_c.json').read_text());tag=selection['run_tag'];assert re.fullmatch('[a-z0-9_]+',tag)
assert selection['independent_DRC']==selection['antenna_nets']==0 and selection['all_signal_geometry_connected']
stage=json.loads((C/'reports/runtime_final_route_c_odb.json').read_text());assert stage['sha256']==selection['source_sha256']
state=json.loads((C/'runs'/tag/'1-openroad-detailedrouting/state_out.json').read_text());state.update(odb='/runtime/final_route_c.odb',metrics={},sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('gds','klayout_gds','spef','def'):state.pop(key,None)
(C/'final_post_state_b.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_working.json').read_text());assert cfg['KLAYOUT_CONFLICT_RESOLUTION']=='OverwriteCell'
cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','KLayout.StreamOut','KLayout.DRC','OpenROAD.CheckAntennas','OpenROAD.RCX']}
cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc';cfg['DECAP_CELLS']=[]
(C/'config_focus_post_b.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('FINAL_POST_CHECKED_INPUT_READY',tag,selection['source_sha256'])
