"""Verify SRAM abstraction and core LVS with the corrected full-macro stream."""
from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
state=json.loads((C/'runs/pg_stream_d/2-klayout-drc/state_out.json').read_text())
assert state['metrics']['klayout__drc_error__count']==0
state.update(odb='/runtime/pg_via_d.odb',gds='/runtime/pg_d.gds',klayout_gds='/runtime/pg_d.gds',metrics={})
state['def']='/runtime/pg_via_d.def'
state.pop('spef',None)
(C/'pg_d_lvs_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_working.json').read_text())
assert cfg['MAGIC_EXT_ABSTRACT_CELLS']==['^sky130_sram_2kbyte_1rw1r_32x512_8$']
cfg['meta']={'version':2,'flow':['Magic.SpiceExtraction','Netgen.LVS']}
(C/'config_pg_d_lvs.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('Full corrected-macro PG_D core/abstract-SRAM LVS probe prepared; not final signal candidate.')
