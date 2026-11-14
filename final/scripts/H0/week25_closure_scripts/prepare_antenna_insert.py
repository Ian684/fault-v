"""Prepare native diode insertion on the proven signal/PG rebase."""
from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
proof=json.loads((C/'reports/focus_pg_rebase.json').read_text());assert proof['PG_geometry_exactly_matches_selected_PG'] and proof['all_cells_graph_signal_wire_bytes_guides_obstructions_unchanged']
state=json.loads((C/'focus_post_state.json').read_text());assert state['odb']=='/runtime_final/focus_pg.odb'
state['metrics']={};(C/'antenna_insert_state.json').write_text(json.dumps(state,indent=2)+'\n')
config=json.loads((C/'config_working.json').read_text());config['meta']={'version':2,'flow':['OpenROAD.DetailedRouting']};config['DRT_THREADS']=4
(C/'config_antenna_insert.json').write_text(json.dumps(config,indent=2)+'\n')
print('PG-rebased antenna insertion prepared; original cells must remain fixed.')
