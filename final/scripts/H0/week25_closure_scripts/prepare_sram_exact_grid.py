"""Preserve all manufactured polygons; remove only redundant off-grid pin annotations."""
from pathlib import Path
from collections import Counter
import hashlib,json,pya
C=Path('/work/week25_closure');(C/'controls').mkdir(exist_ok=True)
source=Path('/work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.gds')
old=pya.Layout();old.read(str(source));assert old.dbu==.001
new=pya.Layout();new.dbu=.005
mapping={cell.cell_index():new.create_cell(cell.name) for cell in old.each_cell()}
scale=pya.ICplxTrans(.2,0,False,0,0);inverse=pya.ICplxTrans(5,0,False,0,0)
removed=Counter();kept=0;texts=0;instances=0
for cell in old.each_cell():
    target=mapping[cell.cell_index()]
    for li in old.layer_indices():
        info=old.get_info(li);idx=new.layer(info)
        for polygon in pya.Region(cell.shapes(li)).each():
            points=list(polygon.each_point_hull())
            for h in range(polygon.holes()):points+=list(polygon.each_point_hole(h))
            if any(p.x%5 or p.y%5 for p in points):
                assert info.layer in (68,69) and info.datatype==16,str(info)
                drawing_index=old.find_layer(info.layer,20);assert drawing_index is not None
                drawing=pya.Region(cell.shapes(drawing_index));drawing.merge()
                assert (pya.Region(polygon)-drawing).is_empty(),(cell.name,str(info),'pin marker exceeds drawing')
                removed[str(info)]+=1
                continue
            converted=polygon.transformed(scale)
            assert str(converted.transformed(inverse))==str(polygon)
            target.shapes(idx).insert(converted);kept+=1
        for shape in cell.shapes(li).each():
            if shape.is_text():
                texts+=1
    for inst in cell.each_inst():
        tr=inst.cplx_trans;p=tr.disp
        assert p.x%5==p.y%5==0
        converted=pya.ICplxTrans(tr.mag,tr.angle,tr.is_mirror(),p.x//5,p.y//5)
        if inst.is_regular_array():
            assert all(v.x%5==v.y%5==0 for v in (inst.a,inst.b))
            replica=pya.CellInstArray(mapping[inst.cell_index].cell_index(),converted,pya.Vector(inst.a.x//5,inst.a.y//5),pya.Vector(inst.b.x//5,inst.b.y//5),inst.na,inst.nb)
        else:replica=pya.CellInstArray(mapping[inst.cell_index].cell_index(),converted)
        target.insert(replica);instances+=1
assert kept>100000 and instances==33981
path=C/'controls/SRAM_exact_5nm.gds';new.write(str(path))
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'source_dbu_um':old.dbu,'output_dbu_um':new.dbu,'manufactured_polygons_exact_roundtrip':kept,'texts_omitted_for_geometry_only_DRC':texts,'instance_transforms_preserved':instances,'removed_redundant_offgrid_pin_polygons':dict(removed),'all_removed_annotations_contained_by_same_cell_actual_metal':True,'scope':'Diagnostic representation change. No manufactured mask geometry changed; removed redundant pin markers only after polygon containment proof. Text omitted; not a production macro or LVS replacement.'}
(C/'reports/SRAM_exact_grid.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
