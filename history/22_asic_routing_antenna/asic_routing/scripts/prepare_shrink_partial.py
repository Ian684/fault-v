"""Prepare a coherent BUF2 ECO source with net- and geometry-driven preclearance."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,struct,re,odb
R=Path("/work/routing")
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=read(R/"reports/neighbor_trial_preserved.json")
source=R/record["snapshot"];report=R/record["report"]
repaired=R/"runs/shrink_rc/final/odb/fault_v_asic_top.odb"
assert sha(source)==record["snapshot_sha256"] and sha(report)==record["report_sha256"]
probe=read(R/"reports/diagnostic_buf2_result.json")
assert sha(R/"runs/shrink_rc/final/nl/fault_v_asic_top.nl.v")==probe["probe_sha256"]
def load(p):
 d=odb.dbDatabase.create();odb.read_db(d,str(p));return d,d.getChip().getBlock()
repaired_sha=sha(repaired)
od,ob=load(source);nd,nb=load(repaired)
def bbox(q):return(q.xMin(),q.yMin(),q.xMax(),q.yMax())
def cells(b):
 return{i.getName():(i.getMaster().getName(),bbox(i.getBBox()),str(i.getOrient()),str(i.getPlacementStatus())) for i in b.getInsts()}
def graph(b):
 return{n.getName():(str(n.getSigType()),tuple(sorted((t.getInst().getName(),t.getMTerm().getName()) for t in n.getITerms())),tuple(sorted(t.getName() for t in n.getBTerms()))) for n in b.getNets()}
oldcells,newcells=cells(ob),cells(nb);oldgraph,newgraph=graph(ob),graph(nb)
assert oldgraph==newgraph and set(oldcells)==set(newcells)
changed={n for n in oldcells if oldcells[n]!=newcells[n]}
assert len(changed)==105
regions=[]
for name in changed:
 old,new=oldcells[name],newcells[name]
 assert old[0]=="sky130_fd_sc_hd__buf_4" and new[0]=="sky130_fd_sc_hd__buf_2" and old[2:]==new[2:]
 a,c=old[1],new[1];assert a[0]<=c[0] and a[1]<=c[1] and a[2]>=c[2] and a[3]>=c[3]
 regions.append(c)
for name in ["_30188_","_37463_","_37409_"]:assert oldcells[name]==newcells[name]
m=nd.findMaster("sky130_fd_sc_hd__buf_2");boxes=list(m.getObstructions())
for t in m.getMTerms():
 for pin in t.getMPins():boxes.extend(pin.getGeometry())
layers={x.getTechLayer().getName() for x in boxes if x.getTechLayer()}
assert layers&{"met1","met2","met3","met4","met5"}=={"met1"}
u=nb.getDbUnitsPerMicron();halo=u;tile=20*u;grid=defaultdict(list)
for x,y,x2,y2 in regions:
 q=(x-halo,y-halo,x2+halo,y2+halo)
 for tx in range(q[0]//tile,q[2]//tile+1):
  for ty in range(q[1]//tile,q[3]//tile+1):grid[tx,ty].append(q)
def intersect(a,c):
 return a[0]<=c[2] and c[0]<=a[2] and a[1]<=c[3] and c[1]<=a[3]
assert intersect((-100,500,1100,500),(0,0,1000,1000))
assert intersect((500,-100,500,1100),(0,0,1000,1000))
assert not intersect((0,2000,1000,2000),(0,0,1000,1000))
def near(x,y,x2,y2):
 q=(min(x,x2),min(y,y2),max(x,x2),max(y,y2))
 return any(intersect(q,r) for tx in range(q[0]//tile,q[2]//tile+1) for ty in range(q[1]//tile,q[3]//tile+1) for r in grid.get((tx,ty),()))
incident={n for n,g in newgraph.items() if g[0] not in ["POWER","GROUND"] and any(i in changed for i,p in g[1])}
reported={n for n in set(re.findall(r"\bnet:(\S+)",report.read_text())) if newgraph[n][0] not in ["POWER","GROUND"]}
geometric=set();base_dirty=incident|reported
# shortcut: M1 neighbor preclear uses centerlines plus a1um halo; use full polygons if final DRC reveals missed neighbors.
for n in nb.getNets():
 if n.getSigType() in ["POWER","GROUND"] or n.getName() in base_dirty:continue
 w=n.getWire()
 if w is None:continue
 dec=odb.dbWireDecoder();dec.begin(w);junctions={};layer=None;previous=None
 while True:
  op=dec.next()
  if op==dec.END_DECODE:break
  if op==dec.PATH:layer=dec.getLayer().getName();previous=None
  elif op in [dec.POINT,dec.POINT_EXT]:
   point=tuple((dec.getPoint_ext() if op==dec.POINT_EXT else dec.getPoint())[:2])
   a=previous if previous is not None else point
   if layer=="met1" and near(*a,*point):geometric.add(n.getName());break
   previous=point;junctions[dec.getJunctionId()]=(point,layer)
  elif op==dec.JUNCTION:previous,layer=junctions[dec.getJunctionValue()]
  elif op in [dec.SHORT,dec.VWIRE]:layer=dec.getLayer().getName();previous=None
  elif op in [dec.TECH_VIA,dec.VIA]:
   newlayer=dec.getLayer().getName()
   if previous is not None and "met1" in [layer,newlayer] and near(*previous,*previous):
    geometric.add(n.getName());break
   layer=newlayer;junctions[dec.getJunctionId()]=(previous,layer)
dirty=incident|reported|geometric
def wire_hash(w):
 if w is None:return None
 h=hashlib.sha256()
 for j in range(w.length()):h.update(struct.pack("<BI",w.getOpcode(j),w.getData(j)&0xffffffff))
 return h.hexdigest()
retained={};removed=[]
for n in nb.getNets():
 if n.getSigType() in ["POWER","GROUND"]:continue
 name=n.getName();w=n.getWire()
 if name in dirty:
  if w is not None:odb.dbWire.destroy(w);removed.append(name)
 else:
  assert wire_hash(w)==wire_hash(ob.findNet(name).getWire()),("Unexpected untouched wire change",name)
  if w is not None:retained[name]=wire_hash(w)
assert cells(nb)==newcells and graph(nb)==newgraph and len(retained)>39000
partial=R/"inputs/shrink_rc_partial.odb";assert not partial.exists();odb.write_db(nd,str(partial))
assert sha(source)==record["snapshot_sha256"] and sha(repaired)==repaired_sha
# Global guides use a separate route-free copy. No route solutions are spliced.
for n in nb.getNets():
 if n.getSigType() not in ["POWER","GROUND"] and n.getWire() is not None:odb.dbWire.destroy(n.getWire())
grt=R/"inputs/shrink_rc_grt.odb";assert not grt.exists();odb.write_db(nd,str(grt))
out={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"repaired":str(repaired.relative_to(R)),"repaired_sha256":sha(repaired),"native_drc_report":str(report.relative_to(R)),"native_drc_report_sha256":sha(report),"partial":str(partial.relative_to(R)),"partial_sha256":sha(partial),"grt":str(grt.relative_to(R)),"grt_sha256":sha(grt),"shrunk_instances":sorted(changed),"incident_nets":sorted(incident),"native_reported_nets":sorted(reported),"M1_neighbor_nets":sorted(geometric),"dirty_nets":sorted(dirty),"removed_wire_count":len(removed),"retained_wire_count":len(retained),"retained_wire_sha256":retained,"graph_unchanged":True,"footprints_subset":True,"other_cells_unchanged":True,"scope":"One coherent native checkpoint,105 BUF4->BUF2 footprint subsets only; invalidate incident nets, all prior native-DRC signal/clock nets and M1 centerline/via neighbors in1um halos. Remaining wires exact original checkpoint opcodes/data. A separate route-free copy is only for guides. All actual final native/RCX/STA3.1/calibrated independent DRC gates required."}
(R/"reports/shrink_rc_partial_input.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k not in ["retained_wire_sha256","shrunk_instances","incident_nets","native_reported_nets","M1_neighbor_nets","dirty_nets"]},indent=2))
print("NET_COUNTS",{"incident":len(incident),"reported":len(reported),"M1_neighbors":len(geometric),"total":len(dirty)})
