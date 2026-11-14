"""Use the calibrated SRAM pin interface on the actual compact-PG manufacturing stream."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
assert (C/'logs/pg_f_stream_a.exit').read_text().strip()=='0'
run=C/'runs/pg_f_stream_a';assert json.loads((run/'native_archive_manifest.json').read_text())['all_byte_exact']
state=json.loads((run/'2-klayout-drc/state_out.json').read_text());assert state['metrics']['klayout__drc_error__count']==0
gds=run/'1-klayout-streamout/fault_v_asic_top.gds'
view=json.loads((C/'reports/pg_f_core_lvs_view.json').read_text())
with gds.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==view['manufacturing_source_GDS_sha256']
assert len(view['pin_names'])==125
state.update(odb='/runtime_final/pg_compact_f.odb',gds='/runtime/pg_f_core_lvs.gds',klayout_gds='/runtime/pg_f_core_lvs.gds',metrics={});state['def']='/runtime_final/pg_compact_f.def';state.pop('spef',None)
cfg=json.loads((C/'config_working.json').read_text());assert cfg['MAGIC_EXT_ABSTRACT_CELLS']==['^sky130_sram_2kbyte_1rw1r_32x512_8$'];cfg['meta']={'version':2,'flow':['Magic.SpiceExtraction','Netgen.LVS']}
for name,value in [('pg_f_core_lvs_state.json',state),('config_pg_f_core_lvs.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
print('PG_E_CALIBRATED_CORE_LVS_INPUT_READY',flush=True)
