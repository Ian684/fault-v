from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
state=json.loads((C/'runs/stream_fix_a/1-klayout-streamout/state_out.json').read_text())
proof=json.loads((C/'reports/streamed_SRAM_geometry_fixed.json').read_text())
assert proof['all_selected_manufacturing_layers_exact'] and sum(proof['referenced_macro_instances'].values())==18
state['metrics']={}
(C/'correct_stream_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C.parent/'week25_front/config_check.json').read_text())
cfg['meta']={'version':2,'flow':['KLayout.DRC']}
(C/'config_correct_stream_checks.json').write_text(json.dumps(cfg,indent=2)+'\n')
