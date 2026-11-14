from pathlib import Path
import json,pya
C=Path('/work/week25_closure');L=pya.Layout()
L.read('/work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.gds')
macro=L.cell('sky130_sram_2kbyte_1rw1r_32x512_8')
child=L.cell('sky130_sram_2kbyte_1rw1r_32x512_8_control_logic_r')
assert macro is not None and child is not None
def metal(cell):
    region=pya.Region()
    for index in L.layer_indices():
        info=L.get_info(index)
        if info.layer==69 and info.datatype not in (5,10,44):region+=pya.Region(cell.begin_shapes_rec(index))
    region.merge();return region
def vias(cell):
    region=pya.Region()
    for layer in (68,69):
        index=L.find_layer(layer,44)
        if index is not None:region+=pya.Region(cell.begin_shapes_rec(index))
    region.merge();return region
local=metal(child);local_vias=vias(child)
global_metal=metal(macro);global_vias=vias(macro)
marker=pya.Region(pya.Box(12770,0,12910,42620))
assert abs(L.dbu-.001)<1e-12
transformed=marker.transformed(pya.ICplxTrans(1,180,False,670410,399020))
component=global_metal.interacting(transformed);component.merge()
assert not component.is_empty()
result={'native_full_DRC_marker':'m2.x in control_logic_r, x12.77..12.91 y0..42.62 um','child_floating_components':local.not_interacting(local_vias).count(),'macro_global_floating_components':global_metal.not_interacting(global_vias).count(),'marker_connected_component_polygons':component.count(),'marker_connected_component_area_um2':component.area()*L.dbu**2,'marker_component_interacts_with_via':not component.interacting(global_vias).is_empty(),'scope':'Explicit flat manufactured metal connectivity context; no geometry or rule change.'}
(C/'reports/macro_floating_context.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
