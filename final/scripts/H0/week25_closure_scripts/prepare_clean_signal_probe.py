"""Check the actual DRC-clean signal geometry electrically before the final PG/diode merge."""
from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
selection=json.loads((C/'reports/signal_selection.json').read_text());assert selection['independent_DRC']==0 and selection['all_signal_geometry_connected']
assert selection['source_sha256']==json.loads((C/'reports/manual_export_binding.json').read_text())['native_final_sha256']
state=json.loads((C/'runs'/selection['run_tag']/'1-openroad-detailedrouting/state_out.json').read_text());state.update(odb='/runtime/signal_closed.odb',metrics={},sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('spef','def','gds','klayout_gds'):state.pop(key,None)
cfg=json.loads((C/'config_working.json').read_text());cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','OpenROAD.CheckAntennas','OpenROAD.RCX']};cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc';cfg['PL_OPTIMIZE_MIRRORING']=False;cfg['DECAP_CELLS']=[]
for name,value in [('clean_signal_probe_state.json',state),('config_clean_signal_probe_rc.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
code=(C/'scripts/prepare_focus_probe_sta.py').read_text().replace('focus_probe_rc_a','clean_signal_rc_a').replace('focus_probe_sta','clean_signal_sta')
p=C/'scripts/prepare_clean_signal_sta.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
(C/'reports/clean_signal_probe_input.json').write_text(json.dumps({'source_sha256':selection['source_sha256'],'independent_signal_DRC':0,'all_signal_geometry_connected':True,'includes_explicit_3p05um_LI1_bridge':True,'accepted_for_final':False,'scope':'Fresh three-RC extraction and TT STA on the actual clean signal route. Final selected PG and actual diode/fill geometry still require the common-candidate repeat.'},indent=2)+'\n')
print('CLEAN_SIGNAL_ELECTRICAL_PROBE_READY',selection['source_sha256'])
