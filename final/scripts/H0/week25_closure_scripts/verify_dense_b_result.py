"""Reject empty/misconfigured zero reports using six actual dummy-layer controls."""
from pathlib import Path
from collections import Counter
import hashlib,json,subprocess,xml.etree.ElementTree as ET,pya
C=Path('/work/week25_closure');deck=C/'controls/sky130_fill_interaction_tiled.drc'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
coverage=json.loads((C/'reports/fill_tiled_screen_coverage.json').read_text())
assert sha(deck)==coverage['tiled_deck_sha256']
assert (C/'logs/dense_b_checks.exit').read_text().strip()=='0'
l=pya.Layout();l.dbu=.001;top=l.create_cell('fault_v_asic_top')
top.shapes(l.layer(81,2)).insert(pya.Box(0,0,70000,20000))
layers={'LI':(56,28),'M1':(36,28),'M2':(41,28),'M3':(34,28),'M4':(51,28),'M5':(59,28)}
for index,(name,spec) in enumerate(layers.items()):
    x=5000+index*10000;width=100 if name=='M5' else 50
    top.shapes(l.layer(*spec)).insert(pya.Box(x,5000,x+width,7000))
control=C/'controls/fill_beol_negative.gds';assert not control.exists();l.write(str(control))
negative=C/'reports/fill_beol_negative.rdb'
with (C/'logs/fill_beol_negative.log').open('w') as out:
    subprocess.run(['klayout','-b','-r',str(deck),'-rd','input='+str(control),'-rd','top_cell=fault_v_asic_top','-rd','report='+str(negative)],stdout=out,stderr=subprocess.STDOUT,check=True)
def read(path):
    root=ET.parse(path).getroot();assert root.tag=='report-database'
    categories=root.findall('categories/category');assert len(categories)>50
    cells=root.findall('cells/cell');assert cells
    return root.findall('items/item'),categories,cells
bad,_,_=read(negative);counts=Counter(i.findtext('category').strip("'") for i in bad)
required={'LI':('li.1','li.8','MR_li.WID.4'),'M1':('m1.1',),'M2':('m2.1',),'M3':('m3.1',),'M4':('m4.1',),'M5':('m5.1',)}
detected={layer:sum(counts.get(c,0) for c in cats) for layer,cats in required.items()}
assert all(v>0 for v in detected.values()),(counts,detected)
report=C/'reports/dense_b_beol.rdb';items,categories,cells=read(report);assert not items
density=json.loads((C/'reports/dense_fom_native_b_density.json').read_text());fom=json.loads((C/'reports/full_fom_b_geometry.json').read_text())
assert density['all_numeric_density_checks_pass'] and fom['screen_pass']
composition=json.loads((C/'dense_fom_native_b/filled.gds.gz.json').read_text())
assert composition['base_sha256']==density['base_sha256'] and composition['original_top_references_unchanged'] and composition['fill_only_on_eight_canonical_dummy_purposes']
sample,_,_=read(C/'reports/fill_sample_tiled.rdb');assert len(sample)==29
record={'accepted_for_development_baseline':True,'final_signal_candidate':False,'numeric_density_layers':7,'windows_each':1053,'FOM_full_geometry_pass':True,'full_BEOL_marker_count':len(items),'reported_categories':len(categories),'reported_cells':len(cells),'all_six_dummy_width_negative_controls_detected':detected,'negative_control_total_markers':len(bad),'prior_unrepaired_sample_markers':29,'source_base_sha256':density['base_sha256'],'source_fill_sha256':density['fill_sha256'],'full_BEOL_report_sha256':sha(report),'negative_control_GDS_sha256':sha(control),'negative_control_report_sha256':sha(negative),'deck_sha256':sha(deck),'scope':coverage['scope']+' Development F baseline only. Final drive/PG implementation must regenerate fill and rerun these gates.'}
(C/'reports/dense_b_verified.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
