"""Invalidate every wire affected by the actual-RC ECO; never merge route solutions."""
from pathlib import Path
import hashlib,json,struct,odb
R=Path("/work/routing")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads((R/"reports/rc_followup_insert_plan.json").read_text())
source=R/plan["source"]
repaired=R/"runs/rc_followup_insert_v2/final/odb/fault_v_asic_top.odb"
assert sha(source)==plan["source_sha256"]
def read(path):
 d=odb.dbDatabase.create();odb.read_db(d,str(path));return d,d.getChip().getBlock()
od,ob=read(source);nd,nb=read(repaired)
def cells(b):
 return {i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation()),str(i.getPlacementStatus())) for i in b.getInsts()}
def graph(b):
 return {n.getName():(str(n.getSigType()),tuple(sorted((t.getInst().getName(),t.getMTerm().getName()) for t in n.getITerms())),tuple(sorted(t.getName() for t in n.getBTerms()))) for n in b.getNets()}
def dirty_set(oldcells,newcells,oldgraph,newgraph):
 changed={n for n in set(oldcells)|set(newcells) if oldcells.get(n)!=newcells.get(n)}
 return {n for n,g in newgraph.items() if oldgraph.get(n)!=g or any(i in changed for i,p in g[1])},changed
# A moved load, resized driver, and newly split sink net must all invalidate routes.
a={"driver":("buf1",0),"load":("gate",0),"other":("buf1",0)}
z={"driver":("buf4",0),"load":("gate",1),"other":("buf1",0)}
g={"d":("SIGNAL",(("driver","X"),),()),"l":("SIGNAL",(("load","A"),),()),"o":("SIGNAL",(("other","X"),),())}
h=dict(g,split=("SIGNAL",(("load","B"),),()))
assert dirty_set(a,z,g,h)[0]=={"d","l","split"}
oldcells,newcells=cells(ob),cells(nb);oldgraph,newgraph=graph(ob),graph(nb)
dirty,changed=dirty_set(oldcells,newcells,oldgraph,newgraph)
assert len(set(newcells)-set(oldcells))==2 and not(set(oldcells)-set(newcells))
for name,old,new in plan["resize"]:
 assert oldcells[name][0]==old and newcells[name][0]==new
for name in ["_30188_","_37463_","_37409_"]:
 assert oldcells[name]==newcells[name],("Pin access ECO moved",name)
def wire_hash(w):
 if w is None:return None
 h=hashlib.sha256()
 for j in range(w.length()):h.update(struct.pack("<BI",w.getOpcode(j),w.getData(j)&0xffffffff))
 return h.hexdigest()
retained={};removed=[];wireless=[]
for n in nb.getNets():
 name=n.getName()
 if n.getSigType() in ["POWER","GROUND"]:continue
 w=n.getWire()
 if name in dirty:
  if w is not None:odb.dbWire.destroy(w);removed.append(name)
  continue
 original=ob.findNet(name);assert original is not None
 assert oldgraph[name]==newgraph[name]
 assert wire_hash(w)==wire_hash(original.getWire()),("Unexpected untouched route change",name)
 if w is not None:retained[name]=wire_hash(w)
 else:wireless.append(name)
assert len(retained)>40000 and dirty and removed
assert cells(nb)==newcells and graph(nb)==newgraph
out=R/"inputs/followup_rc_partial.odb";assert not out.exists()
odb.write_db(nd,str(out))
assert sha(source)==plan["source_sha256"]
audit={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"repaired":str(repaired.relative_to(R)),"repaired_sha256":sha(repaired),"derived":str(out.relative_to(R)),"derived_sha256":sha(out),"changed_instances":sorted(changed),"dirty_nets":sorted(dirty),"removed_wires":removed,"retained_wire_count":len(retained),"retained_wire_sha256":retained,"other_wireless_nets":wireless,"repaired_cells_and_graph_preserved":True,"scope":"Same actual-RC ECO database, invalidate every net touching any resized/moved/new instance or changed connectivity; retain only exact original-baseline wire opcodes/data for untouched nets. No independently routed wire transplants. All acceptance gates still required."}
(R/"reports/followup_rc_partial_input.json").write_text(json.dumps(audit,indent=2)+"\n")
print("DIRECT_RC_PARTIAL",json.dumps({k:v for k,v in audit.items() if k not in ["retained_wire_sha256","dirty_nets","changed_instances","removed_wires","other_wireless_nets"]}))
print("CHANGED_INSTANCES",len(changed),"DIRTY_NETS",len(dirty),"REMOVED",len(removed))
