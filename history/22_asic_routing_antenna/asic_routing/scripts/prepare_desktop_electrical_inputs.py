"""Retain only physically valid routes after the measured electrical proposal."""
from pathlib import Path
import ast,hashlib,json,struct,odb
R=Path('/work/routing');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'runs/routed_desktop_clock_top_full_20261022_084820/final/odb/fault_v_asic_top.odb';proposal=R/'runs/desktop_electrical_proposal/final/odb/fault_v_asic_top.odb'
assert sha(source)=='6e6c419fe047ffac2b428b59e8b1af9df785ef5fd235ae4c70d489f20aaa1976'
for name,names in [('prepare_cold_corner_reguide.py',{'wires','obstructions'}),('prepare_desktop_checkpoint45.py',{'fixed'})]:
 tree=ast.parse((R/'scripts'/name).read_text(encoding='utf-8-sig'));fs=[q for q in tree.body if isinstance(q,ast.FunctionDef) and q.name in names];assert len(fs)==len(names);exec(compile(ast.Module(body=fs,type_ignores=[]),name,'exec'))
def load(p):
 d=odb.dbDatabase.create();odb.read_db(d,str(p));return d,d.getChip().getBlock()
sd,sb=load(source);d,b=load(proposal)
sc,sg,spg=fixed(sb);pc,pg,ppg=fixed(b)
new={'eco_desktop_nor_load10466','eco_desktop_hold_a10467','eco_desktop_hold_b10468','eco_desktop_hold_c10469'};assert set(pc)-set(sc)==new and set(sc)<=set(pc),('actual_added',sorted(set(pc)-set(sc)),'removed',sorted(set(sc)-set(pc)))
for name in new:assert pc[name][0]==('sky130_fd_sc_hd__buf_4' if name.startswith('eco_desktop_nor') else 'sky130_fd_sc_hd__buf_1')
plan=json.loads((R/'reports/desktop_source2_driver_plan.json').read_text());sizes={g['instance']:(g['master'],g['next_master']) for g in plan if g['next_master']};assert len(sizes)==13
resized={k for k in sc if sc[k][0]!=pc[k][0]};assert resized==set(sizes)
for k,(old,after) in sizes.items():assert sc[k][0]==old and pc[k][0]==after
assert spg==ppg and obstructions(sb)==obstructions(b)
for k in sc:
 if sb.findInst(k).getMaster().getType()=='BLOCK':assert sc[k]==pc[k],('Macro changed',k)
for k in ['_30188_','_37463_','_37409_']:assert sc[k]==pc[k]
changed={k for k in pc if k not in sc or sc[k][:3]!=pc[k][:3]}
affected={'net6158','net3262','_15298_'}
for block in [sb,b]:
 for name in changed:
  i=block.findInst(name)
  if i:
   for t in i.getITerms():
    n=t.getNet()
    if n and str(n.getSigType()) not in ['POWER','GROUND']:affected.add(n.getName())
for name in set(sg)|set(pg):
 if sg.get(name)!=pg.get(name):
  n=b.findNet(name)
  if n and str(n.getSigType()) not in ['POWER','GROUND']:affected.add(name)
original=wires(sb);proposal_wires=wires(b);retained={k:v for k,v in original.items() if k not in affected}
assert all(proposal_wires.get(k)==v for k,v in retained.items()),'Unaffected native wires changed'
for name in affected:
 n=b.findNet(name)
 if n and n.getWire():odb.dbWire.destroy(n.getWire())
assert wires(b)==retained
roi=(1581900,640200,1583200,640650);box=lambda q:(q.xMin(),q.yMin(),q.xMax(),q.yMax());hit=lambda q:q[0]<roi[2] and q[2]>roi[0] and q[1]<roi[3] and q[3]>roi[1]
for i in b.getInsts():
 if hit(box(i.getBBox())):
  for t in i.getITerms():assert not any(hit(box(q)) for layer,q in t.getGeometries()),('Keepout covers pin',i.getName(),t.getMTerm().getName())
assert odb.dbObstruction_create(b,d.getTech().findLayer('met1'),*roi)
identity=fixed(b);obs=obstructions(b)
partial=R/'inputs/desktop_electrical_partial.odb';global_input=R/'inputs/desktop_electrical_global.odb';assert not partial.exists() and not global_input.exists();odb.write_db(d,str(partial))
for n in b.getNets():
 if n.getWire():odb.dbWire.destroy(n.getWire())
assert not wires(b) and fixed(b)==identity and obstructions(b)==obs
odb.write_db(d,str(global_input))
state={'odb':str(global_input),'metrics':{}}
for key in ['nl','pnl','sdc','json_h','vh']:
 fs=list((R/'runs/desktop_electrical_proposal/final'/key).glob('*'));assert len(fs)==1;state[key]='/work/routing/'+fs[0].relative_to(R).as_posix()
(R/'desktop_electrical_global_state.json').write_text(json.dumps(state,indent=2)+'\n')
a={'accepted':False,'source':source.relative_to(R).as_posix(),'source_sha256':sha(source),'proposal':proposal.relative_to(R).as_posix(),'proposal_sha256':sha(proposal),'partial':partial.relative_to(R).as_posix(),'partial_sha256':sha(partial),'global_input':global_input.relative_to(R).as_posix(),'global_input_sha256':sha(global_input),'resized_instances':sizes,'added_buffers':sorted(new),'changed_physical_cells':sorted(changed),'cleared_whole_nets':sorted(affected),'retained_wire_count':len(retained),'retained_native_wire_hashes_unchanged':True,'same_partial_and_global_cells_graph_pg_obstructions':True,'original_macros_and_pg_unchanged':True,'pinless_met1_keepout_dbu':roi,'scope':'Electrical and hold ECO proposal from measured routed RC. All wires incident to changed physical cells or changed graph, plus three corner/access nets, are removed completely. Unaffected wires remain byte identical. Actual routing, RC, timing and independent full-chip DRC remain required.'}
(R/'reports/desktop_electrical_input.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a,indent=2),flush=True)
