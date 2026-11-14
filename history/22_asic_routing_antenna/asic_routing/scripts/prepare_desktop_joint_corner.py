"""Jointly reroute the small physical neighborhood of the final short."""
from pathlib import Path
from collections import Counter
import ast,hashlib,json,struct,odb
R=Path('/work/routing');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'runs/routed_desktop_corner_refined_20261025_114634/final/odb/fault_v_asic_top.odb';assert sha(source)=='d998bdc61d1629f981f65e77fa077ddd2273b514ab4875afaa1c2df2d4562ace'
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','obstructions'}),('export_local_shapes.py',{'primitives'}),('prepare_cold_corner_keepout.py',{'shapes','box','hit'})]:
 tree=ast.parse((R/'scripts'/file).read_text(encoding='utf-8-sig'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
 exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
db=odb.dbDatabase.create();odb.read_db(db,str(source));b=db.getChip().getBlock();tech=db.getTech();before=fixed(b);before_wires=wires(b);before_obs=Counter(obstructions(b));assert len(before_wires)==41337
# Remove only our optional routing rectangle; original macro and technology obstructions remain.
optional=('met1',1581900,640280,1582860,640650)
found=[o for o in b.getObstructions() if (o.getBBox().getTechLayer().getName(),*box(o.getBBox()))==optional];assert len(found)==1
odb.dbObstruction.destroy(found[0]);after_obs=Counter(obstructions(b));assert before_obs-after_obs==Counter({optional:1}) and not after_obs-before_obs
region=[1581800,638000,1584800,641500];margin=500;roi=[region[0]-margin,region[1]-margin,region[2]+margin,region[3]+margin];layers={'met1','met2','met3','met4'}
dirty={'net3179','net5465','_15298_'};intersections={}
for n in b.getNets():
 w=n.getWire()
 if w is None:continue
 assert n.getNonDefaultRule() is None
 hits=[(l,z) for l,z in shapes(w) if l in layers and hit(z,roi)]
 if hits:dirty.add(n.getName());intersections[n.getName()]=hits
assert 3<=len(dirty)<80,('Neighborhood size outside guard',len(dirty))
for name in sorted(dirty):
 n=b.findNet(name);assert n and n.getWire() and str(n.getSigType()) in ['SIGNAL','CLOCK'];odb.dbWire.destroy(n.getWire())
retained={n:v for n,v in before_wires.items() if n not in dirty};assert wires(b)==retained and fixed(b)==before
partial=R/'inputs/desktop_joint_corner_partial.odb';grt=R/'inputs/desktop_joint_corner_grt.odb';report=R/'reports/desktop_joint_corner_input.json';assert not any(p.exists() for p in [partial,grt,report]);odb.write_db(db,str(partial))
for n in b.getNets():
 if n.getWire():assert str(n.getSigType()) in ['SIGNAL','CLOCK'];odb.dbWire.destroy(n.getWire())
assert wires(b)=={} and fixed(b)==before and Counter(obstructions(b))==after_obs;odb.write_db(db,str(grt))
state=json.loads((R/'desktop_corner_refined_global_state.json').read_text(encoding='utf-8'));state['odb']=str(grt);(R/'desktop_joint_corner_global_state.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
a={'accepted':False,'source':source.relative_to(R).as_posix(),'source_sha256':sha(source),'partial':partial.relative_to(R).as_posix(),'partial_sha256':sha(partial),'grt':grt.relative_to(R).as_posix(),'grt_sha256':sha(grt),'region_dbu':region,'margin_dbu':margin,'routing_layers':sorted(layers),'cleared_whole_nets':sorted(dirty),'retained_wire_count':len(retained),'retained_wire_sha256':retained,'intersecting_shapes':intersections,'cells_graph_pg_unchanged':True,'all_original_macro_technology_obstructions_preserved':True,'removed_only_our_optional_obstruction':optional,'scope':'Release complete real signal/clock nets crossing a small 3x3.5um neighborhood plus500nm margin acrossmet1-met4, including both sides of the final short and access workaround. Keep every other native wire opcode exactly. Remove only our optional routing rectangle; no original technology/macros/rules/pins/PG modified. Actual full global0, native and independent DRC0, RC/STA and phase/PG checks remain mandatory.'}
report.write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8');assert sha(source)==a['source_sha256'];print(json.dumps({k:v for k,v in a.items() if k not in ['retained_wire_sha256','intersecting_shapes']},indent=2))
