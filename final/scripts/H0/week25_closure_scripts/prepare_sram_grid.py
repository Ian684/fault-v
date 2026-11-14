"""Test Magic's GDS grid conversion using a provably identical 5nm representation."""
from pathlib import Path
import hashlib,json,pya
C=Path('/work/week25_closure')
(C/'controls').mkdir(exist_ok=True)
source=Path('/work/week25_signoff/controls/SRAM_tiled.gds')
old=pya.Layout();old.read(str(source));assert old.dbu==.001
top=old.cell('sky130_sram_2kbyte_1rw1r_32x512_8')
new=pya.Layout();new.dbu=.005
mapping={cell.cell_index():new.create_cell(cell.name) for cell in old.each_cell()}
scale=pya.ICplxTrans(.2,0,False,0,0)
vertices=0
for cell in old.each_cell():
    target=mapping[cell.cell_index()]
    for li in old.layer_indices():
        idx=new.layer(old.get_info(li))
        region=pya.Region(cell.shapes(li))
        for polygon in region.each():
            for point in polygon.each_point_hull():
                assert point.x%5==point.y%5==0,(cell.name,old.get_info(li),str(point))
                vertices+=1
            for hole in range(polygon.holes()):
                for point in polygon.each_point_hole(hole):
                    assert point.x%5==point.y%5==0,(cell.name,str(point))
            target.shapes(idx).insert(polygon.transformed(scale))
    for inst in cell.each_inst():
        assert inst.trans==pya.Trans() and not inst.is_regular_array()
        target.insert(pya.CellInstArray(mapping[inst.cell_index].cell_index(),pya.Trans()))
checked=0
for li in old.layer_indices():
    a=pya.Region(top.begin_shapes_rec(li));a.merge()
    b=pya.Region(mapping[top.cell_index()].begin_shapes_rec(new.layer(old.get_info(li))))
    b.transform(pya.ICplxTrans(5,0,False,0,0));b.merge()
    assert (a^b).is_empty(),str(old.get_info(li))
    checked+=1
path=C/'controls/SRAM_tiled_5nm.gds';new.write(str(path))
result={'all_drawing_layers_XOR_empty':True,'layers':checked,'vertices_on_5nm_grid':vertices,'source_dbu_um':.001,'output_dbu_um':.005,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':'Exact geometry; different file DBU only. Diagnostic does not replace SRAM or waive a rule.'}
(C/'reports/SRAM_grid_equivalence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result),flush=True)
