"""Require final-source binding, calibrated geometry rules and every density window."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads((C/p).read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert (C/'logs/final_fill.exit').read_text().strip()=='0'
stage=read('reports/runtime_final_core_gds.json');generation=read('final_fill/generation.json')
density=read('reports/final_sliding_density.json');grid=read('reports/final_dummy_grid.json');fom=read('reports/final_fom_geometry.json')
composition=read('final_fill/filled.gds.gz.json');calibration=read('reports/dense_b_verified.json')
assert density['base_sha256']==generation['source_sha256']==composition['base_sha256']==stage['sha256']
assert density['all_numeric_density_checks_pass'] and fom['screen_pass']
assert density['windows_per_layer']==1053 and len(density['layers'])==8
numeric={n:v for n,v in density['layers'].items() if v['limits'][0] is not None};assert len(numeric)==7
assert all(len(row['windows'])==1053 for row in density['layers'].values())
assert all(row['failed_windows']==0 and row['global_pass'] for row in numeric.values())
assert fom['source_sha256']==density['base_sha256'] and fom['fill_sha256']==density['fill_sha256']==grid['fill_sha256']
assert len(fom['tiles'])==20
assert len(grid['layers'])==8 and all(v['offgrid_markers']==0 for v in grid['layers'].values())
assert composition['original_top_references_unchanged'] and composition['fill_only_on_eight_canonical_dummy_purposes']
assert all(v>0 for v in calibration['all_six_dummy_width_negative_controls_detected'].values())
deck=C/'controls/sky130_fill_interaction_tiled.drc';assert sha(deck)==calibration['deck_sha256']
assert sha(C/'controls/fill_beol_negative.gds')==calibration['negative_control_GDS_sha256']
assert sha(C/'reports/fill_beol_negative.rdb')==calibration['negative_control_report_sha256']
report=C/'reports/final_fill_beol.rdb';root=ET.parse(report).getroot()
assert root.tag=='report-database' and len(root.findall('categories/category'))>50 and root.findall('cells/cell')
assert not root.findall('items/item')
filled=C/'final_fill/filled.gds.gz'
assert sha(filled)==composition['composite_sha256']
record={'source_final_core_GDS_sha256':stage['sha256'],'final_filled_GDS_sha256':sha(filled),'all_numeric_density_checks_pass':True,'numeric_layers':7,'windows_each':1053,'all_eight_dummy_layers_on_5nm_grid':True,'FOM_geometry_pass':True,'full_BEOL_fill_interaction_markers':0,'calibrated_six_layer_negative_controls_pass':True,'deck_sha256':sha(deck),'BEOL_report_sha256':sha(report),'manufacturing_artifact':'final_fill/filled.gds.gz','scope':'Final common-candidate fill geometry and open-rule sliding-density screens. RCX is demonstrably insensitive to dbFill; qualified fill-aware PEX and full foundry rule/SRAM/package signoff remain uncovered.'}
out=C/'reports/final_fill_verified.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n')
print('FINAL_FILL_DENSITY_GEOMETRY_PASS',record['final_filled_GDS_sha256'],flush=True)
