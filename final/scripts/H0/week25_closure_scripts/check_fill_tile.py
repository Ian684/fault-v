from pathlib import Path
import json,pya
C=Path('/work/week25_closure');base=pya.Layout();fill=pya.Layout()
base.read(str(C/'fill_tile_trial/fault_v_asic_top.gds'));fill.read(str(C/'fill_tile_trial/fault_v_asic_top_fill_pattern.gds.gz'))
top=base.cell('fault_v_asic_top');filled=fill.top_cell();assert top is not None and filled is not None
assert hasattr(top,'begin_shapes_rec_overlapping')
box=pya.Box(0,0,round(700/base.dbu),round(700/base.dbu));area=box.area()
def region(layout,cell,spec):
    result=pya.Region();clip=pya.Box(0,0,round(700/layout.dbu),round(700/layout.dbu))
    for layer,datatype in spec:
        index=layout.find_layer(layer,datatype)
        if index is not None:result+=pya.Region(cell.begin_shapes_rec_overlapping(index,clip))
    result.transform(pya.ICplxTrans(layout.dbu/base.dbu,0,False,0,0));result&=pya.Region(box);result.merge()
    return result
layers={'LI':(67,56,.35,.60),'MET1':(68,36,.35,.60),'MET2':(69,41,.35,.60),'MET3':(70,34,.35,.60),'MET4':(71,51,.35,.60),'MET5':(72,59,.45,.76)}
result={'scope':'Native PDK wafflefill, first 700um square only; no full-chip density or fill-aware PEX claim.','fill_dbu_um':fill.dbu,'fill_layers':[str(i) for i in fill.layer_infos()],'layers':{}}
for name,(drawing,dummy,lower,upper) in layers.items():
    a=region(base,top,[(drawing,20),(dummy,28)])
    b=region(fill,filled,[(dummy,28),(drawing,99)])
    density=(a|b).area()/area
    result['layers'][name]={'before':a.area()/area,'fill':b.area()/area,'combined':density,'screen_pass':lower<=density<=upper,'same_material_overlap_um2':(a&b).area()*base.dbu**2}
    print(name,result['layers'][name],flush=True)
    (C/'reports/fill_tile_density.json').write_text(json.dumps(result,indent=2)+'\n')
assert len(result['layers'])==6
