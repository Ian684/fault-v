from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
trim=json.loads((C/'reports/macro_orphan_trim.json').read_text())
macro=C/'macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim.gds'
assert hashlib.sha256(macro.read_bytes()).hexdigest()==trim['output_sha256']
cfg=json.loads((C.parent/'week25_front/config_check.json').read_text())
name='sky130_sram_2kbyte_1rw1r_32x512_8'
cfg['MACROS'][name]['gds']=['/work/week25_closure/macros/'+macro.name]
cfg['KLAYOUT_CONFLICT_RESOLUTION']='OverwriteCell'
cfg['meta']={'version':2,'flow':['KLayout.StreamOut','KLayout.DRC']}
(C/'config_trim_check.json').write_text(json.dumps(cfg,indent=2)+'\n')
working=dict(cfg);working['meta']={'version':2,'flow':['OpenROAD.FillInsertion','KLayout.StreamOut','KLayout.DRC']}
(C/'config_working.json').write_text(json.dumps(working,indent=2)+'\n')
