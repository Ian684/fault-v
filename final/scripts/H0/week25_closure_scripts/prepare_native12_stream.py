from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
stage=json.loads((C/'reports/runtime_antenna_native12_odb.json').read_text());assert stage['sha256']==json.loads((C/'reports/antenna_iter12_probe.json').read_text())['source_sha256']
state=json.loads((C/'antenna_route_state.json').read_text());state.update(odb='/runtime/antenna_native12.odb',metrics={},sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('spef','def','gds','klayout_gds'):state.pop(key,None)
cfg=json.loads((C/'config_working.json').read_text());cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','KLayout.StreamOut']};cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc';cfg['DECAP_CELLS']=[]
for name,value in [('native12_stream_state.json',state),('config_native12_stream.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
print('NATIVE12_STREAM_PROBE_PREPARED',flush=True)
