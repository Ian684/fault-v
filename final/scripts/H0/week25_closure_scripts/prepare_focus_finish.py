"""Bounded DRC-only repair of the seven remaining route shorts, with unchanged cells."""
from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
pair=json.loads((C/'runs/focus_unfixed_a/1-openroad-detailedrouting/native_pair.json').read_text());assert pair['native_DRC']==7
state=json.loads((C/'runs/focus_unfixed_a/1-openroad-detailedrouting/state_out.json').read_text());state['odb']='/runtime/focus_finish_input.odb';state['metrics']={}
for key in ('gds','klayout_gds','spef','def'):state.pop(key,None)
(C/'focus_finish_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_focus_route.json').read_text());(C/'config_focus_finish.json').write_text(json.dumps(cfg,indent=2)+'\n')
cli=(C/'scripts/cached_route_cli.py').read_text().replace('scripts/cached_detailed.tcl','scripts/focus_finish.tcl')
(C/'scripts/focus_finish_cli.py').write_text(cli,newline='\n')
print('Seven-short local repair ready; same 50-driver placement, no rule changes.')
