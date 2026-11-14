"""Remove only dummy LI islands that fail the native core-marker intersection rule."""
from pathlib import Path
import hashlib,json,sys,pya
basefile,fillfile,target,report=map(Path,sys.argv[1:5]);assert not target.exists()
base=pya.Layout();fill=pya.Layout();base.read(str(basefile));fill.read(str(fillfile))
assert base.dbu==fill.dbu;u=fill.dbu;bt=base.cell('fault_v_asic_top');ft=fill.top_cell()
def region(layout,cell,spec):
    result=pya.Region()
    for layer,dt in spec:
        index=layout.find_layer(layer,dt)
        if index is not None:result+=pya.Region(cell.begin_shapes_rec(index))
    result.merge();return result
li=region(fill,ft,[(67,99),(56,28)]);ce=region(base,bt,[(81,2)])
markers=(li&ce).width_check(round(.14/u));removed=li.interacting(markers.polygons(1));good=li-removed
assert not removed.is_empty() and ((good|removed)^li).is_empty()
assert (good&ce).width_check(round(.14/u)).is_empty() and good.width_check(round(.17/u)).is_empty()
other={(i.layer,i.datatype):region(fill,ft,[(i.layer,i.datatype)]) for i in fill.layer_infos() if (i.layer,i.datatype) not in ((67,99),(56,28))};assert len(other)==7
for spec in ((67,99),(56,28)):
    idx=fill.find_layer(*spec)
    if idx is not None:
        for cell in fill.each_cell():cell.shapes(idx).clear()
ft.shapes(fill.layer(67,99)).insert(good)
for spec,previous in other.items():assert (previous^region(fill,ft,[spec])).is_empty(),spec
fill.write(str(target))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'source_geometry_sha256':sha(basefile),'input_fill_sha256':sha(fillfile),'output_fill_sha256':sha(target),'native_li8_markers_before':markers.size(),'removed_LI_dummy_islands':removed.size(),'removed_LI_area_um2':removed.area()*u*u,'native_li8_markers_after':0,'full_LI_dummy_minimum_width_screen_pass':True,'all_other_seven_fill_layers_XOR_empty':True,'scope':'Removes whole dummy LI islands whose intersection with existing areaid.ce fails native li.8. No circuit LI or core markers modified, and no DRC category disabled. Global density and final native interaction checks remain required.'}
report.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
