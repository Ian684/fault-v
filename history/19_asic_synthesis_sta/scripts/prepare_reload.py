from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]
assert tag.replace('_','').isalnum()
states=list((R/'runs'/tag).glob('*-openroad-staprepnr/state_out.json'))
assert len(states)==1
state=json.loads(states[0].read_text())
state['nl']='/work/design/eco/fault_v_asic_top.nl.v'
(R/'eco/reload_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((R/'config.json').read_text())
del cfg['STA_EXTRA_CORNER_TCL_FILE']
(R/'config_reload.json').write_text(json.dumps(cfg,indent=2)+'\n')
