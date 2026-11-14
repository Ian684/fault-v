"""Remove exact coincident, unlabeled SRAM child instances; preserve every mask polygon."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys,pya
source,target,report=map(Path,sys.argv[1:4]);assert source.is_file() and not target.exists()
name='sky130_sram_2kbyte_1rw1r_32x512_8'
a=pya.Layout();a.read(str(source));b=pya.Layout();b.read(str(source))
am=a.cell(name);bm=b.cell(name);assert am and bm
original_specs={(i.layer,i.datatype) for i in a.layer_infos()}
changes=[]
for cell in b.each_cell():
    if not cell.name.startswith(name):continue
    seen=set();unique=[];duplicates=[];instances=list(cell.each_inst())
    for inst in instances:
        cia=inst.cell_inst
        for trans in cia.each_cplx_trans():
            key=(cia.cell_index,trans.to_s(),inst.prop_id)
            if key in seen:
                child=b.cell(cia.cell_index)
                for li in b.layer_indexes():
                    it=child.begin_shapes_rec(li)
                    while not it.at_end():
                        assert not it.shape().is_text(),('Duplicate contains a label',cell.name,child.name)
                        it.next()
                duplicates.append({'child':child.name,'transform':trans.to_s(),'property_id':inst.prop_id})
            else:seen.add(key);unique.append((cia.cell_index,trans,inst.prop_id))
    if not duplicates:continue
    for inst in instances:inst.delete()
    for child,trans,prop in unique:
        inst=cell.insert(pya.CellInstArray(child,trans));inst.prop_id=prop
    changes.append({'parent':cell.name,'removed_exact_coincident_unlabeled_instances':duplicates})
assert changes,'No exact duplicates found'
checks={}
for spec in sorted(original_specs):
    ai=a.find_layer(*spec);bi=b.find_layer(*spec)
    ar=pya.Region(am.begin_shapes_rec(ai));br=pya.Region(bm.begin_shapes_rec(bi))
    assert (ar^br).is_empty(),('Mask geometry changed',spec)
    if not ar.is_empty():checks[f'{spec[0]}/{spec[1]}']=True
assert len(checks)==39,len(checks)
def labels(layout,cell):
    found=Counter()
    for li in layout.layer_indexes():
        info=layout.get_info(li);it=cell.begin_shapes_rec(li)
        while not it.at_end():
            s=it.shape()
            if s.is_text():found[(info.layer,info.datatype,s.text.transformed(it.itrans()).to_s())]+=1
            it.next()
    return found
assert labels(a,am)==labels(b,bm),'Text/port labels changed'
topa=a.cell('fault_v_asic_top');topb=b.cell('fault_v_asic_top')
if topa:
    assert Counter(i.cell_inst.to_s() for i in topa.each_inst())==Counter(i.cell_inst.to_s() for i in topb.each_inst())
    assert sum(a.cell(i.cell_index).name==name for i in topa.each_inst())==18
target.parent.mkdir(parents=True,exist_ok=True);b.write(str(target))
# Reopen the actual exported artifact and repeat mask geometry checks.
reopened=pya.Layout();reopened.read(str(target));rm=reopened.cell(name);assert rm
for spec in sorted(original_specs):
    assert (pya.Region(am.begin_shapes_rec(a.find_layer(*spec)))^pya.Region(rm.begin_shapes_rec(reopened.find_layer(*spec)))).is_empty()
assert labels(a,am)==labels(reopened,rm)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
record={'source_sha256':sha(source),'output_sha256':sha(target),'modified_parent_cells':len(changes),'removed_exact_instances':sum(len(x['removed_exact_coincident_unlabeled_instances']) for x in changes),'all_39_macro_polygon_layers_XOR_equal_after_reopen':True,'all_flattened_text_port_labels_identical':True,'core_top_instance_array_records_unchanged':bool(topa),'changes':changes,'scope':'Hierarchy-only deduplication of identical cell/transform/property instances without text. No mask geometry, pin label, standard cell or core placement change; no SRAM internal qualification implied.'}
report.write_text(json.dumps(record,indent=2)+'\n');print('SRAM_DUPLICATE_INSTANCE_REPAIR',record['removed_exact_instances'],sha(target),flush=True)
