from pathlib import Path
import hashlib,json,shutil
C=Path(__file__).resolve().parents[1]
snapshots=sorted((C/'runs/minimal_route_a/1-openroad-detailedrouting').glob('drt_iter*.odb'),key=lambda p:p.stat().st_mtime_ns)
assert len(snapshots)>=2
source=snapshots[-2];stamp=source.stat().st_mtime_ns
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
digest=sha(source);target=C/'inputs/timing_probe_a.odb';assert not target.exists()
shutil.copyfile(source,target)
assert sha(target)==digest and source.stat().st_mtime_ns==stamp and sha(source)==digest
state=json.loads((C/'route_state.json').read_text());state['odb']='/work/week25_closure/inputs/timing_probe_a.odb';state['metrics']={}
(C/'probe_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_global.json').read_text())
cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','OpenROAD.CheckAntennas','OpenROAD.RCX']}
cfg['DECAP_CELLS']=[]
(C/'config_probe_rc.json').write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/timing_probe_input.json').write_text(json.dumps({'source':str(source),'source_sha256':digest,'copied_stable_checkpoint':True,'accepted':False,'scope':'Completed route checkpoint for electrical feedback only; route DRC not closed and no final GDS acceptance claimed.'},indent=2)+'\n')
print('Stable timing probe',source.name,digest,flush=True)
