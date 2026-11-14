"""Check actual transformed dummy geometry on the pinned PDK manufacturing grid."""
from pathlib import Path
import gc,hashlib,json,re,sys,pya
source,report=map(Path,sys.argv[1:3]);C=Path('/work/week25_closure')
tlef=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef'
grid_um=float(re.search(r'MANUFACTURINGGRID\s+([0-9.]+)',tlef.read_text())[1]);assert grid_um==.005
l=pya.Layout();l.read(str(source));top=l.top_cell();assert top and len(l.top_cells())==1
grid=round(grid_um/l.dbu);assert grid>0 and abs(grid*l.dbu-grid_um)<1e-12
assert pya.Region(pya.Box(0,0,grid*20,grid*20)).grid_check(grid,grid).is_empty()
assert not pya.Region(pya.Box(1,0,grid*20+1,grid*20)).grid_check(grid,grid).is_empty()
specs={'FOM':[(65,99),(23,28)],'POLY':[(66,99),(28,28)],'LI':[(67,99),(56,28)],'M1':[(68,99),(36,28)],'M2':[(69,99),(41,28)],'M3':[(70,99),(34,28)],'M4':[(71,99),(51,28)],'M5':[(72,99),(59,28)]};results={}
for name,spec in specs.items():
    r=pya.Region()
    for a,z in spec:
        index=l.find_layer(a,z)
        if index is not None:r+=pya.Region(top.begin_shapes_rec(index))
    assert not r.is_empty(),name
    errors=r.grid_check(grid,grid).size();results[name]={'polygons':r.size(),'offgrid_markers':errors};print('DUMMY_GRID',name,results[name],flush=True)
    del r;gc.collect()
with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
passed=all(r['offgrid_markers']==0 for r in results.values())
report.write_text(json.dumps({'fill_sha256':digest,'grid_um':grid_um,'layers':results,'positive_and_negative_controls_pass':True,'screen_pass':passed,'scope':'All eight dummy purposes, after recursive instance transforms. Manufacturing-grid screen only; not foundry dummy qualification.'},indent=2)+'\n');assert passed
