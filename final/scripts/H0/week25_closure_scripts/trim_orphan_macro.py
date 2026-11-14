"""Remove the one measured isolated M2 component; prove the exact mask delta."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,pya
C=Path('/work/week25_closure');(C/'macros').mkdir(exist_ok=True)
source=Path('/work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.gds')
lef=Path('/work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef').read_text()
pins={m[1]:m[2] for m in re.finditer(r'\bPIN\s+(\S+)(.*?)\n\s+END\s+\1(?=\s)',lef,re.S)}
assert len(pins)==125
pin_layers=Counter(layer for body in pins.values() for layer in re.findall(r'\bLAYER\s+(\w+)\s*;',body))
assert not any(re.search(r'\bLAYER\s+met2\s*;',body) for body in pins.values()),'A top-level M2 pin needs separate interface analysis'
before=pya.Layout();before.read(str(source));after=pya.Layout();after.read(str(source))
name='sky130_sram_2kbyte_1rw1r_32x512_8';child_name=name+'_control_logic_r'
top0=before.cell(name);top1=after.cell(name);child=after.cell(child_name)
assert before.dbu==after.dbu==.001 and child is not None
marker=pya.Region(pya.Box(12770,0,12910,42620))
expected=marker.transformed(pya.ICplxTrans(1,180,False,670410,399020))
def region(layout,cell,layer,datatype):
    index=layout.find_layer(layer,datatype)
    r=pya.Region(cell.begin_shapes_rec(index)) if index is not None else pya.Region()
    r.merge();return r
m2=region(before,top0,69,20)
vias=region(before,top0,68,44)|region(before,top0,69,44)
component=m2.interacting(expected);component.merge()
assert (component^expected).is_empty() and component.interacting(vias).is_empty()
assert abs(component.area()*.001**2-5.9668)<1e-9
changes={}
for datatype in (20,16):
    index=after.find_layer(69,datatype)
    if index is None:continue
    shapes=child.shapes(index)
    direct=pya.Region(shapes);direct.merge()
    removed=direct&marker
    if removed.is_empty():continue
    assert datatype!=20 or (removed^marker).is_empty(),'Physical stripe not a direct, isolated component'
    texts=[shape.text for shape in shapes.each() if shape.is_text()]
    for shape in list(shapes.each()):
        if not shape.is_text():shape.delete()
    shapes.insert(direct-marker)
    assert len([shape for shape in shapes.each() if shape.is_text()])==len(texts)
    changes[f'69/{datatype}']=removed.area()*.001**2
assert '69/20' in changes
layer_proofs={}
for info in before.layer_infos():
    a=region(before,top0,info.layer,info.datatype);b=region(after,top1,info.layer,info.datatype)
    delta=a^b
    if info.layer==69 and info.datatype in (20,16):
        assert (delta-expected).is_empty(),str(info)
    else:assert delta.is_empty(),str(info)
    layer_proofs[str(info)]={'XOR_area_um2':delta.area()*.001**2,'unchanged':delta.is_empty()}
assert (region(after,top1,69,20).not_interacting(vias)).is_empty()
output=C/'macros'/f'{name}.orphan_trim.gds';assert not output.exists();after.write(str(output))
result={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'changes_um2':changes,'all_other_drawing_layers_XOR_empty':True,'layer_proofs':layer_proofs,'global_component_had_no_same_layer_connection_or_via':True,'LEF_top_pin_layers':dict(pin_layers),'LEF_has_no_M2_top_pin':True,'source_master':child_name,'local_rectangle_um':[12.77,0,12.91,42.62],'scope':'One isolated non-pin M2 strip removed in a versioned macro copy. Devices, gate/diffusion, top-level pin interface and all other mask geometry unchanged. Inherited analytical TT model is not promoted to foundry-qualified characterization.'}
(C/'reports/macro_orphan_trim.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='layer_proofs'},indent=2),flush=True)
