"""Remove complete dummy islands that fail public FOM minimum-width/implant screens."""
from pathlib import Path
import hashlib,json,sys,pya
basefile,fillfile,target,report=map(Path,sys.argv[1:5]);assert not target.exists()
base=pya.Layout();fill=pya.Layout();base.read(str(basefile));fill.read(str(fillfile))
assert base.dbu==fill.dbu;u=fill.dbu;bt=base.cell('fault_v_asic_top');ft=fill.top_cell()
assert bt is not None and ft is not None
def region(layout,cell,spec,box=None):
    r=pya.Region()
    for layer,dt in spec:
        index=layout.find_layer(layer,dt)
        if index is not None:
            iterator=cell.begin_shapes_rec(index) if box is None else cell.begin_shapes_rec_overlapping(index,box)
            r+=pya.Region(iterator)
    if box is not None:r&=pya.Region(box)
    r.merge();return r
fom=region(fill,ft,[(65,99),(23,28)]);assert not fom.is_empty()
box=fom.bbox().enlarged(round(1/u))
implant=region(base,bt,[(93,44),(94,20)],box)
bad_width=fom.width_check(round(.5/u)).polygons(1)
removed=fom.interacting(bad_width)|fom.interacting(implant.sized(round(.13/u)))
good=fom-removed;good.merge()
assert not removed.is_empty() and (good&removed).is_empty() and ((good|removed)^fom).is_empty()
assert good.width_check(round(.5/u)).is_empty()
assert good.separation_check(implant,round(.13/u)).is_empty()
assert good.space_check(round(.4/u)).is_empty()
other={(info.layer,info.datatype):region(fill,ft,[(info.layer,info.datatype)]) for info in fill.layer_infos() if (info.layer,info.datatype) not in ((65,99),(23,28))}
assert len(other)==7
for spec in ((65,99),(23,28)):
    idx=fill.find_layer(*spec)
    if idx is not None:
        for cell in fill.each_cell():cell.shapes(idx).clear()
idx=fill.layer(65,99);ft.shapes(idx).insert(good)
assert (region(fill,ft,[(65,99)])^good).is_empty()
for spec,previous in other.items():
    assert (previous^region(fill,ft,[spec])).is_empty(),spec
fill.write(str(target))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record={'input_sha256':sha(fillfile),'output_sha256':sha(target),'source_geometry_sha256':sha(basefile),'removed_FOM_islands':removed.size(),'removed_FOM_area_um2':removed.area()*u*u,'retained_FOM_area_um2':good.area()*u*u,'all_other_seven_fill_layers_XOR_empty':True,'width_spacing_implant_screens_pass':True,'scope':'Deletes only whole unconnected FOM dummy islands that intersect <0.5um width markers or 0.13um implant keepouts. No source circuit geometry changes. Existing foundry qualification, seal/frame and macro internal signoff are not inferred.'}
report.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
