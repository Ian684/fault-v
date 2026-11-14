"""Electrical feedback from a stable full-route checkpoint, never final acceptance."""
from pathlib import Path
import hashlib,json,shutil,time
C=Path(__file__).resolve().parents[1]
source=C/'runs/focus_unfixed_a/1-openroad-detailedrouting/drt_iter9.odb'
stamp=source.stat().st_mtime_ns;assert time.time()-source.stat().st_mtime>60
target=C/'inputs/timing_focus_probe.odb';assert not target.exists()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
digest=sha(source)
with source.open('rb') as f,target.open('wb') as out:shutil.copyfileobj(f,out,1024*1024)
assert digest==sha(target)==sha(source) and source.stat().st_mtime_ns==stamp
state=json.loads((C/'full_route_state.json').read_text());state['odb']='/runtime/timing_focus_probe.odb';state['metrics']={}
for key in ('spef','def','gds','klayout_gds'):state.pop(key,None)
(C/'focus_probe_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_probe_rc.json').read_text());(C/'config_focus_probe_rc.json').write_text(json.dumps(cfg,indent=2)+'\n')
script=(C/'scripts/prepare_post_sta.py').read_text().replace('post_route_a','focus_probe_rc_a').replace('/7-openroad-rcx/','/3-openroad-rcx/').replace('post_sta','focus_probe_sta')
(C/'scripts/prepare_focus_probe_sta.py').write_text(script,newline='\n')
(C/'reports/timing_focus_probe_input.json').write_text(json.dumps({'source':str(source),'source_sha256':digest,'stable_checkpoint_copied_exactly':True,'accepted':False,'scope':'50-driver electrical feedback only. Native route still has DRVs; no final candidate acceptance.'},indent=2)+'\n')
print('Stable 50-driver checkpoint copied',digest)
