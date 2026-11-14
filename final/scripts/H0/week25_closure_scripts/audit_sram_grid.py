from pathlib import Path
from collections import Counter
import json,pya
C=Path('/work/week25_closure');L=pya.Layout()
L.read('/work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.gds')
bad=Counter();examples={};vertices=0;transforms=0
for cell in L.each_cell():
    for li in L.layer_indices():
        layer=str(L.get_info(li))
        for polygon in pya.Region(cell.shapes(li)).each():
            for point in polygon.each_point_hull():
                vertices+=1
                if point.x%5 or point.y%5:
                    bad[layer]+=1
                    examples.setdefault(layer,{'cell':cell.name,'point':str(point)})
    for inst in cell.each_inst():
        transforms+=1
        p=inst.cplx_trans.disp
        if p.x%5 or p.y%5:bad['instance_transform']+=1;examples.setdefault('instance_transform',{'cell':cell.name,'transform':str(inst.cplx_trans)})
        if inst.is_regular_array():
            for vector in (inst.a,inst.b):
                if vector.x%5 or vector.y%5:bad['array_vector']+=1
assert vertices>1000 and transforms>0
result={'source_dbu_um':L.dbu,'vertices':vertices,'transforms':transforms,'off_5nm_counts':dict(bad),'examples':examples}
(C/'reports/SRAM_source_grid.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
