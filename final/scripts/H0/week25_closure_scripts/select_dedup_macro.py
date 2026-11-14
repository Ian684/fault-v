"""Bind future stream-out to the exact geometry-preserving SRAM hierarchy repair."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1];proof=json.loads((C/'reports/macro_dedup.json').read_text())
assert proof['removed_exact_instances']==268 and proof['all_39_macro_polygon_layers_XOR_equal_after_reopen'] and proof['all_flattened_text_port_labels_identical']
macro=C/'macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim_dedup.gds'
with macro.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
assert digest==proof['output_sha256']
path=C/'config_working.json';cfg=json.loads(path.read_text());entry=cfg['MACROS']['sky130_sram_2kbyte_1rw1r_32x512_8']
assert len(entry['gds'])==1 and entry['gds'][0].endswith(('.orphan_trim.gds','.orphan_trim_dedup.gds'))
entry['gds']=['/work/week25_closure/macros/'+macro.name]
path.write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/working_macro_selection.json').write_text(json.dumps({'macro':macro.name,'sha256':digest,'all_39_mask_layers_and_labels_unchanged':True,'future_streamout_only':True,'scope':'268 exact coincident unlabeled child instances removed. All prior source files and completed runs preserved.'},indent=2)+'\n')
print('WORKING_MACRO_SELECTED',digest)
