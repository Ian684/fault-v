from pathlib import Path
import json,pya
C=Path('/work/week25_closure');L=pya.Layout();L.read(str(C/'controls/SRAM_exact_5nm.gds'))
cell=L.cell('sky130_fd_bd_sram__openram_dp_cell');assert cell is not None
out=pya.Layout();out.dbu=L.dbu;top=out.create_cell('faultv_bitcell');top.copy_tree(cell)
out.write(str(C/'controls/bitcell.gds'))
data={'dbu_um':L.dbu,'bbox_um':[v*L.dbu for v in (cell.bbox().left,cell.bbox().bottom,cell.bbox().right,cell.bbox().top)],'layers':{}}
for layer,datatype in [(64,20),(65,20),(65,44),(66,20),(66,44),(67,20),(67,44),(68,20),(69,20),(81,20),(82,20),(83,44)]:
    index=L.find_layer(layer,datatype)
    if index is None:continue
    polygons=[]
    for polygon in pya.Region(cell.begin_shapes_rec(index)).each():
        polygons.append([[p.x*L.dbu,p.y*L.dbu] for p in polygon.each_point_hull()])
    if polygons:data['layers'][f'{layer}/{datatype}']=polygons
(C/'reports/bitcell_geometry.json').write_text(json.dumps(data,indent=2)+'\n')
print('Bitcell bounds',data['bbox_um'],flush=True)
