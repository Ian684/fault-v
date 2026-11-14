from pathlib import Path
import hashlib,json,shutil
C=Path(__file__).resolve().parents[1]
state=json.loads((C.parent/'week25_front/working_candidate_state.json').read_text())
source=C.parent/state['gds'].removeprefix('/work/')
assert hashlib.sha256(source.read_bytes()).hexdigest()=='f67fbff8b6646f0f4ec0c91674f185859cff2489e322f923dc2a1eaf035c745a'
folder=C/'fill_trial';folder.mkdir(exist_ok=True)
target=folder/'fault_v_asic_top.gds';assert not target.exists()
shutil.copyfile(source,target)
(C/'reports/fill_trial_input.json').write_text(json.dumps({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Flow-development copy of pre-ECO filler baseline. Not the post-ECO final layout; fill-aware extraction must be qualified separately.'},indent=2)+'\n')
