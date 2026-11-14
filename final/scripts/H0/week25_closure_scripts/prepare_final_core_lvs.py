"""Bind the calibrated pin-interface LVS to the actual final manufacturing stream."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
assert (C/'logs/focus_post_b.exit').read_text().strip()=='0'
run=C/'runs/focus_post_b';assert json.loads((run/'native_archive_manifest.json').read_text())['all_byte_exact']
state=json.loads((run/'3-klayout-drc/state_out.json').read_text())
assert state['metrics']['klayout__drc_error__count']==0
gds=run/'2-klayout-streamout/fault_v_asic_top.gds'
view=json.loads((C/'reports/final_core_lvs_view.json').read_text())
with gds.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==view['manufacturing_source_GDS_sha256']
assert len(view['pin_names'])==125
state.update(gds='/runtime/final_core_lvs.gds',klayout_gds='/runtime/final_core_lvs.gds',metrics={})
state.pop('spef',None)
cfg=json.loads((C/'config_working.json').read_text())
assert cfg['MAGIC_EXT_ABSTRACT_CELLS']==['^sky130_sram_2kbyte_1rw1r_32x512_8$']
cfg['meta']={'version':2,'flow':['Magic.SpiceExtraction','Netgen.LVS']}
for name,value in [('final_core_lvs_state.json',state),('config_final_core_lvs.json',cfg)]:
    p=C/name;assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n')
print('FINAL_CALIBRATED_CORE_LVS_INPUT_READY',flush=True)
