"""Refine our optional keepout and clear the two nets responsible for all source45 shorts."""
from pathlib import Path
from collections import Counter
import ast,json,hashlib,struct,odb
R=Path('/work/routing');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'runs/routed_desktop_electrical_20261023_162420/1-openroad-detailedrouting/drt_iter45.odb'
assert sha(source)=='3c03005b53a6426f37981af107b4e372c26c6ac5abf2143164db81b9aa598006'
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','obstructions'})]:
 tree=ast.parse((R/'scripts'/file).read_text(encoding='utf-8-sig'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
 exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
db=odb.dbDatabase.create();odb.read_db(db,str(source));b=db.getChip().getBlock();tech=db.getTech()
before=fixed(b);before_wires=wires(b);before_obs=Counter(obstructions(b));assert len(before_wires)==41337 and len(b.getInsts())==68982
old=[1581900,640200,1583200,640650];new=[1581900,640280,1582860,640650]
assert old[0]<=new[0]<new[2]<=old[2] and old[1]<=new[1]<new[3]<=old[3]
box=lambda q:[q.xMin(),q.yMin(),q.xMax(),q.yMax()]
found=[o for o in b.getObstructions() if o.getBBox().getTechLayer().getName()=='met1' and box(o.getBBox())==old];assert len(found)==1
odb.dbObstruction.destroy(found[0]);assert odb.dbObstruction_create(b,tech.findLayer('met1'),*new)
after_obs=Counter(obstructions(b));removed=before_obs-after_obs;added=after_obs-before_obs
assert sum(removed.values())==sum(added.values())==1 and fixed(b)==before
names=['_15298_','net3361','net5465']
for name in names:
 n=b.findNet(name);assert n and n.getWire() and str(n.getSigType())=='SIGNAL';odb.dbWire.destroy(n.getWire())
retained={n:v for n,v in before_wires.items() if n not in names};assert wires(b)==retained and len(retained)==41334 and fixed(b)==before
partial=R/'inputs/desktop_corner_refined_partial.odb';grt=R/'inputs/desktop_corner_refined_grt.odb';report=R/'reports/desktop_corner_refined_input.json';assert not any(p.exists() for p in [partial,grt,report])
odb.write_db(db,str(partial))
for n in b.getNets():
 if n.getWire():assert str(n.getSigType()) in ['SIGNAL','CLOCK'];odb.dbWire.destroy(n.getWire())
assert wires(b)=={} and fixed(b)==before and Counter(obstructions(b))==after_obs
odb.write_db(db,str(grt))
state=json.loads((R/'desktop_electrical_global_state.json').read_text(encoding='utf-8'));state['odb']=str(grt);(R/'desktop_corner_refined_global_state.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
a={'accepted':False,'source':source.relative_to(R).as_posix(),'source_sha256':sha(source),'partial':partial.relative_to(R).as_posix(),'partial_sha256':sha(partial),'grt':grt.relative_to(R).as_posix(),'grt_sha256':sha(grt),'cleared_whole_nets':names,'retained_wire_count':len(retained),'other_wires_byte_identical':True,'cells_graph_pg_unchanged':True,'old_optional_met1_keepout':old,'refined_optional_met1_keepout':new,'original_macro_technology_obstructions_unchanged':True,'scope':'Refine only our one optional block obstruction to a strict subset; preserve all original macro and technology obstructions and rules. Clear complete two shorted nets plus known access workaround. Actual GRT, native DRC, independent DRC, RC and timing remain required.'}
report.write_text(json.dumps(a,indent=2)+'\n',encoding='utf-8');assert sha(source)==a['source_sha256'];print(json.dumps(a,indent=2))
