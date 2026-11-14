from pathlib import Path
from collections import Counter
import json,pya,os
C=Path('/work/week25_closure');source=pya.Layout();core=pya.Layout()
source.read(os.environ.get('AUDIT_MACRO_GDS','/work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.gds'))
state=json.loads(Path('/work/week25_front/working_candidate_state.json').read_text())
core_path=os.environ.get('AUDIT_CORE_GDS',state['gds'])
core.read(core_path);top=core.cell('fault_v_asic_top')
name='sky130_sram_2kbyte_1rw1r_32x512_8';original=source.cell(name)
instances=Counter(core.cell(inst.cell_index).name for inst in top.each_inst() if name in core.cell(inst.cell_index).name)
assert sum(instances.values())==18,dict(instances)
result={'core_gds':core_path,'referenced_macro_instances':dict(instances),'source_dbu':source.dbu,'core_dbu':core.dbu,'masters':{}}
for master in instances:
    cell=core.cell(master);layers={}
    for info in source.layer_infos():
        layer,datatype=info.layer,info.datatype
        aidx=source.find_layer(layer,datatype);bidx=core.find_layer(layer,datatype)
        a=pya.Region(original.begin_shapes_rec(aidx)) if aidx is not None else pya.Region()
        b=pya.Region(cell.begin_shapes_rec(bidx)) if bidx is not None else pya.Region()
        a.merge();b.merge()
        if source.dbu!=core.dbu:b.transform(pya.ICplxTrans(core.dbu/source.dbu,0,False,0,0))
        xor=(a^b)
        layers[f'{layer}/{datatype}']={'source_area_um2':a.area()*source.dbu**2,'streamed_area_um2':b.area()*source.dbu**2,'XOR_empty':xor.is_empty(),'XOR_area_um2':xor.area()*source.dbu**2}
    result['masters'][master]=layers
result['all_selected_manufacturing_layers_exact']=all(v['XOR_empty'] for d in result['masters'].values() for v in d.values())
(C/os.environ.get('AUDIT_REPORT','reports/streamed_SRAM_geometry.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2),flush=True)
