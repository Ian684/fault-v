from pathlib import Path
from collections import Counter
import json,pya
C=Path('/work/week25_closure');source=pya.Layout();fixed=pya.Layout();old=pya.Layout()
source.read('/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds')
fixed.read(str(C/'runs/stream_fix_a/1-klayout-streamout/fault_v_asic_top.gds'))
old.read(json.loads(Path('/work/week25_front/working_candidate_state.json').read_text())['gds'])
top=fixed.cell('fault_v_asic_top');masters=Counter(fixed.cell(i.cell_index).name for i in top.each_inst() if fixed.cell(i.cell_index).name.startswith('sky130_fd_sc_hd__'))
assert sum(masters.values())==215841
result={'instances':sum(masters.values()),'unique_masters':len(masters),'masters':{}}
for name in masters:
    ref=source.cell(name);cell=fixed.cell(name);prior=old.cell(name)
    assert ref is not None and cell is not None and prior is not None,name
    check={}
    for layer,datatype in ((64,20),(65,20),(66,20),(66,44),(67,20),(68,20)):
        ai=source.find_layer(layer,datatype);bi=fixed.find_layer(layer,datatype);ci=old.find_layer(layer,datatype)
        a=pya.Region(ref.begin_shapes_rec(ai)) if ai is not None else pya.Region()
        a.transform(pya.ICplxTrans(source.dbu/fixed.dbu,0,False,0,0));a.merge()
        b=pya.Region(cell.begin_shapes_rec(bi)) if bi is not None else pya.Region();b.merge()
        c=pya.Region(prior.begin_shapes_rec(ci)) if ci is not None else pya.Region();c.merge()
        check[f'{layer}/{datatype}']={'corrected_XOR_empty':(a^b).is_empty(),'prior_XOR_empty':(a^c).is_empty(),'source_area_um2':a.area()*fixed.dbu**2}
    result['masters'][name]=check
result['all_corrected_selected_layers_exact']=all(v['corrected_XOR_empty'] for m in result['masters'].values() for v in m.values())
result['prior_masters_with_mismatch']=[name for name,m in result['masters'].items() if not all(v['prior_XOR_empty'] for v in m.values())]
assert result['all_corrected_selected_layers_exact']
(C/'reports/streamed_stdcell_geometry.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='masters'},indent=2))
