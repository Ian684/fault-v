"""Bind fresh three-RC electrical checks to the independently checked 51-driver ODB."""
from pathlib import Path
import json
from reviewed_drivers import load_driver_review
C=Path(__file__).resolve().parents[1]
selection=json.loads((C/'reports/signal_selection.json').read_text())
assert selection['source_sha256']==json.loads((C/'reports/manual_export51_binding.json').read_text())['native_final_sha256']
drivers,overlay=load_driver_review(C);assert len(drivers)==51 and overlay
state=json.loads((C/'runs'/selection['run_tag']/'1-openroad-detailedrouting/state_out.json').read_text())
state.update(odb=selection['runtime_ODB'],metrics={},sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('spef','def','gds','klayout_gds'):state.pop(key,None)
cfg=json.loads((C/'config_working.json').read_text())
cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','OpenROAD.CheckAntennas','OpenROAD.RCX']}
cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc'
cfg['PL_OPTIMIZE_MIRRORING']=False;cfg['DECAP_CELLS']=[]
for name,value in [('driver51_probe_state.json',state),('config_driver51_probe_rc.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
code=(C/'scripts/prepare_focus_post_sta.py').read_text().replace('focus_post_a/5-openroad-rcx','driver51_rc_a/3-openroad-rcx').replace('focus_post_a','driver51_rc_a').replace('focus_post_sta','driver51_sta')
p=C/'scripts/prepare_driver51_sta.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('DRIVER51_PROBE_READY',selection['source_sha256'],flush=True)
