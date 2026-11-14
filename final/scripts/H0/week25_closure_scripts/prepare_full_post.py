from pathlib import Path
import json,re
C=Path(__file__).resolve().parents[1]
state=json.loads((C/'runs/full_route_a/1-openroad-detailedrouting/state_out.json').read_text())
log=(C/'logs/full_route.log').read_text();counts=re.findall(r'Number of violations\s*=\s*(\d+)',log)
assert counts and int(counts[-1])==0,'Native full route has not closed'
state['metrics']={}
for key in ('gds','klayout_gds','spef'):state.pop(key,None)
(C/'post_route_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_working.json').read_text())
cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','KLayout.StreamOut','KLayout.DRC','Magic.SpiceExtraction','Netgen.LVS','OpenROAD.CheckAntennas','OpenROAD.RCX']}
cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc'
(C/'config_post_route.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('Native full route closed; fresh complete post-route gates prepared.',flush=True)
