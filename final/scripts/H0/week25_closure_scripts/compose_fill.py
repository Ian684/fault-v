from pathlib import Path
import hashlib,json,sys,pya
basefile,fillfile,target=map(Path,sys.argv[1:4]);assert not target.exists()
layout=pya.Layout();layout.read(str(basefile));top=layout.cell('fault_v_asic_top');assert top is not None
original_names={c.name for c in layout.each_cell()};before=[str(i) for i in top.each_inst()]
fill=pya.Layout();fill.read(str(fillfile));fill_names={c.name for c in fill.each_cell()}
assert not (original_names&fill_names) and fill.dbu==layout.dbu
assert len(fill.top_cells())==1
ftop=fill.top_cell().name
allowed={(23,28),(28,28),(56,28),(36,28),(41,28),(34,28),(51,28),(59,28)}
assert {(i.layer,i.datatype) for i in fill.layer_infos()}<=allowed
del fill
layout.read(str(fillfile));assert {c.name for c in layout.each_cell()}==original_names|fill_names
assert before==[str(i) for i in top.each_inst()]
top.insert(pya.CellInstArray(layout.cell(ftop).cell_index(),pya.Trans()))
assert len(list(top.each_inst()))==len(before)+1 and len(layout.top_cells())==1
layout.write(str(target))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
target.with_suffix(target.suffix+'.json').write_text(json.dumps({'base_sha256':sha(basefile),'fill_sha256':sha(fillfile),'composite_sha256':sha(target),'original_cells':len(original_names),'new_fill_cells':len(fill_names),'all_cell_names_disjoint':True,'original_top_references_unchanged':True,'fill_only_on_eight_canonical_dummy_purposes':True,'scope':'Adds only identity-transformed dummy-fill hierarchy. Original manufacturing drawing layers and source cell hierarchy are retained.'},indent=2)+'\n')
print('COMPOSITE_FILL_GDS',target,flush=True)
