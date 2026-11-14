"""Build an explicitly separate SRAM pin-interface view for hierarchical core LVS."""
from pathlib import Path
from collections import Counter
from decimal import Decimal
import ast,hashlib,json,re,sys,pya
C=Path('/work/week25_closure');R=C.parent/'routing'
source,output,negative,report=map(Path,sys.argv[1:5]);assert not output.exists() and not negative.exists()
lef=R/'macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef';name='sky130_sram_2kbyte_1rw1r_32x512_8'
tree=ast.parse((R/'scripts/build_sram_antenna_model.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='pins');exec(compile(ast.Module(body=[node],type_ignores=[]),'existing_LEF_pin_parser','exec'))
pin_bodies=pins(lef.read_text());assert len(pin_bodies)==125
a=pya.Layout();a.read(str(source));macro=a.cell(name);top=a.cell('fault_v_asic_top');assert macro and top
mapping={'met1':68,'met2':69,'met3':70,'met4':71,'met5':72,'li1':67};pin_shapes={};pin_labels=default_labels={}
regions={};interface={};u=Decimal(str(a.dbu))
for pin,body in pin_bodies.items():
    current=None;rectangles=[]
    for m in re.finditer(r'\bLAYER\s+(\S+)\s*;|\bRECT\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*;',body):
        if m[1]:current=m[1];assert current in mapping
        else:
            assert current
            values=[Decimal(v)/u for v in m.groups()[1:]];assert all(v==int(v) for v in values)
            box=pya.Box(*map(int,values));spec=(mapping[current],20)
            if spec not in regions:regions[spec]=pya.Region(macro.begin_shapes_rec(a.find_layer(*spec)))
            assert (pya.Region(box)-regions[spec]).is_empty(),('LEF pin extends outside actual full-GDS metal',pin,current,str(box))
            rectangles.append((spec,box))
    assert rectangles,pin;pin_shapes[pin]=rectangles;pin_labels[pin]=[]
for li in a.layer_indexes():
    spec=a.get_info(li)
    for shape in macro.shapes(li).each():
        if not shape.is_text() or shape.text.string not in pin_shapes:continue
        pin=shape.text.string;position=shape.text.trans.disp
        assert any(s[0]==spec.layer and box.contains(position) for s,box in pin_shapes[pin]),('GDS pin text outside its LEF/metal interface',pin,str(shape.text))
        pin_labels[pin].append(((spec.layer,spec.datatype),pya.Text(shape.text)))
assert all(pin_labels.values()),[p for p,v in pin_labels.items() if not v]
# A shifted signal pin must fail the same full-GDS containment test.
spec,box=pin_shapes['din0[0]'][0];badbox=box.transformed(pya.Trans(1000000,0));assert not (pya.Region(badbox)-regions[spec]).is_empty()
original_top=Counter((a.cell(i.cell_index).name,i.cplx_trans.to_s(),i.na,i.nb,i.a.to_s(),i.b.to_s()) for i in top.each_inst());assert sum(k[0]==name for k in original_top.elements())==18
def create(target,bad):
    work=pya.Layout();work.read(str(source));wm=work.cell(name);wm.clear()
    for pin,rectangles in pin_shapes.items():
        delta=pya.Trans(2000,0) if bad and pin=='din0[0]' else pya.Trans()
        for spec,box in rectangles:wm.shapes(work.layer(*spec)).insert(box.transformed(delta))
        for spec,text in pin_labels[pin]:wm.shapes(work.layer(*spec)).insert(text.transformed(delta))
    result=pya.Layout();result.dbu=work.dbu;rt=result.create_cell('fault_v_asic_top');rt.copy_tree(work.cell('fault_v_asic_top'))
    assert result.cell(name) and not any(result.cell(name).each_inst())
    observed=Counter((result.cell(i.cell_index).name,i.cplx_trans.to_s(),i.na,i.nb,i.a.to_s(),i.b.to_s()) for i in rt.each_inst());assert observed==original_top
    # All chip routing/labels and every reachable standard-cell master remain exact.
    compared=0
    for cell in result.each_cell():
        if cell.name==name:continue
        ref=a.cell(cell.name);assert ref,cell.name
        specs={(i.layer,i.datatype) for i in a.layer_infos()}|{(i.layer,i.datatype) for i in result.layer_infos()}
        for sp in specs:
            ai=a.find_layer(*sp);bi=result.find_layer(*sp)
            ar=pya.Region(ref.shapes(ai)) if ai is not None else pya.Region();br=pya.Region(cell.shapes(bi)) if bi is not None else pya.Region()
            assert (ar^br).is_empty(),('Non-SRAM geometry changed',cell.name,sp)
            at=Counter(s.text.to_s() for s in ref.shapes(ai).each() if s.is_text()) if ai is not None else Counter()
            bt=Counter(s.text.to_s() for s in cell.shapes(bi).each() if s.is_text()) if bi is not None else Counter()
            assert at==bt,('Non-SRAM labels changed',cell.name,sp)
        compared+=1
    result.write(str(target));return compared
compared=create(output,False);assert create(negative,True)==compared
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
record={'manufacturing_source_GDS_sha256':sha(source),'LVS_only_view_sha256':sha(output),'intentional_bad_pin_view_sha256':sha(negative),'LEF_sha256':sha(lef),'pin_names':sorted(pin_shapes),'unique_SRAM_ports':125,'SRAM_instances':18,'all_LEF_pin_rectangles_inside_actual_full_GDS_metal':True,'all_actual_pin_labels_inside_matching_interfaces':True,'chip_routing_standard_cell_geometry_labels_and_top_instances_unchanged':True,'other_cells_compared':compared,'shifted_pin_containment_negative_control_detected':True,'all_source_manufacturing_layers_preserved_in_original_GDS':True,'negative_LVS_case':'din0[0] metal and label shifted +2um in every macro; must fail actual core LVS','scope':'Separate hierarchical core-LVS view with only validated physical SRAM pin rectangles/labels. All standard-cell and chip routing geometry retained. SRAM interior is explicitly opaque and not qualified. Never use this abstract file for manufacturing DRC, antenna, extraction/STA, density, IR/EM or delivery GDS.'}
report.write_text(json.dumps(record,indent=2)+'\n');print('CORE_LVS_INTERFACE_VIEW_READY',125,18,sha(output),flush=True)
