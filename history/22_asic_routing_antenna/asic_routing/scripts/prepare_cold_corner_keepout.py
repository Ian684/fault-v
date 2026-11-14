"""Stricter routing constraints in proven pin-free space; preserve one coherent source."""
from pathlib import Path
from collections import Counter
import ast,hashlib,json,re,struct,odb
R=Path("/work/routing");sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((R/"reports/cold_iter42_diagnostic_source.json").read_text())
source=R/proof["input"]
assert sha(source)==proof["sha256"]=="4572b42676c79eb1c601f8cf08a50ddc2c796181a9fc6ba04e4cd4e19f2b21c7"
rawpath=R/"reports/cold_iter42_raw_drc.json"
raw=json.loads(rawpath.read_text())
markers=[m for m in raw["raw_markers"] if m["layer"]!="li1"]
assert len(markers)==17 and proof["native_drc"]==17
pattern=r"net:(\S+)"
assert re.findall(pattern,"net:a net:b")==["a","b"]
marker_nets=set()
for m in markers:
 ns=re.findall(pattern,m["srcs"]);assert ns,m
 marker_nets.update(ns)
feasibility=R/"reports/corner_keepout_pin_feasibility.json"
f=json.loads(feasibility.read_text())
assert f["source_sha256"]==sha(source)
plans=f["plans"]
assert len(plans)==3 and all(not q["signal_pin_projection_conflicts"] and q["nearby_power_pin_shapes"]==0 for q in plans)
partial=R/"inputs/cold_corner_keepout_partial.odb"
grt=R/"inputs/cold_corner_keepout_grt.odb"
report=R/"reports/cold_corner_keepout_input.json"
assert not any(p.exists() for p in [partial,grt,report])
db=odb.dbDatabase.create();odb.read_db(db,str(source));b=db.getChip().getBlock();tech=db.getTech()
# Reuse the exact fail-closed polygon decoder; never skip an unsupported wire.
codec=R/"scripts/export_local_shapes.py"
tree=ast.parse(codec.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="primitives")
exec(compile(ast.Module(body=[node],type_ignores=[]),str(codec),"exec"))
def box(q):return [q.xMin(),q.yMin(),q.xMax(),q.yMax()]
def hit(a,c):return a[0]<c[2] and a[2]>c[0] and a[1]<c[3] and a[3]>c[1]
assert hit([0,0,2,2],[1,1,3,3]) and not hit([0,0,1,1],[1,0,2,1])
def cells():
 return {i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation()),str(i.getPlacementStatus())) for i in b.getInsts()}
def graph():
 return {n.getName():(str(n.getSigType()),tuple(sorted((t.getInst().getName(),t.getMTerm().getName()) for t in n.getITerms())),tuple(sorted(t.getName() for t in n.getBTerms()))) for n in b.getNets()}
def wires():
 out={}
 for n in b.getNets():
  w=n.getWire()
  if w is None:continue
  h=hashlib.sha256()
  for j in range(w.length()):h.update(struct.pack("<BI",w.getOpcode(j),w.getData(j)&0xffffffff))
  out[n.getName()]=h.hexdigest()
 return out
def pg_shapes():
 out=[]
 for n in b.getNets():
  for sw in n.getSWires():
   for q in sw.getWires():
    out.append((n.getName(),str(q.getWireShapeType()),str(q.isVia()),tuple(box(q)),q.getTechVia().getName() if q.isVia() and q.getTechVia() else q.getBlockVia().getName() if q.isVia() else q.getTechLayer().getName()))
 return sorted(out)
before_cells=cells();before_graph=graph();before_wires=wires();before_pg=pg_shapes()
assert len(before_wires)>41000 and len(before_cells)==68978
# Check every actual pin layer, including li1 and all boundary pins, with 300nm margin.
for p in plans:
 z=p["box"];roi=[z[0]-300,z[1]-300,z[2]+300,z[3]+300]
 for i in b.getInsts():
  if not hit(box(i.getBBox()),roi):continue
  for t in i.getITerms():
   for l,q in t.getGeometries():assert not hit(box(q),roi),("pin in keepout",p["name"],i.getName(),t.getMTerm().getName(),l.getName())
 for t in b.getBTerms():
  for bp in t.getBPins():
   for q in bp.getBoxes():assert not hit(box(q),roi),("boundary pin",p["name"],t.getName())
def shapes(w):
 ps,_=primitives(w)
 for v in ps:
  if v[0]=="S":
   _,l,x1,y1,x2,y2,e1,e2=v;h=tech.findLayer(l).getWidth()//2
   assert x1==x2 or y1==y2,("non-Manhattan",v)
   yield l,([x1-h,y1-e1,x2+h,y2+e2] if x1==x2 else [x1-e1,y1-h,x2+e2,y2+h])
  elif v[0]=="R":yield v[1],list(v[2:6])
  elif v[0] in ["T","V"]:
   _,name,x,y=v;via=tech.findVia(name) if v[0]=="T" else b.findVia(name);assert via
   for q in via.getBoxes():yield q.getTechLayer().getName(),[q.xMin()+x,q.yMin()+y,q.xMax()+x,q.yMax()+y]
  else:raise AssertionError(v)
regions=[]
for p in plans:
 z=p["box"];roi=[z[0]-500,z[1]-500,z[2]+500,z[3]+500]
 regions.extend((l,roi,p["name"]) for l in p["layers"])
dirty=set(marker_nets);intersections={p["name"]:set() for p in plans};decoded=0
for n in b.getNets():
 w=n.getWire()
 if w is not None:
  assert n.getNonDefaultRule() is None,("NDR requires width-aware codec",n.getName())
  decoded+=1
  for l,z in shapes(w):
   for layer,roi,name in regions:
    if l==layer and hit(z,roi):dirty.add(n.getName());intersections[name].add(n.getName())
 for sw in n.getSWires():
  for q in sw.getWires():
   if q.isVia():
    via=q.getTechVia() or q.getBlockVia();x,y=q.getViaXY()
    fixed=[(z.getTechLayer().getName(),[z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y]) for z in via.getBoxes()]
   else:fixed=[(q.getTechLayer().getName(),box(q))]
   for l,z in fixed:
    for layer,roi,name in regions:
     assert l!=layer or not hit(z,roi),("keepout too near fixed special wire",name,n.getName(),l,z)
assert decoded==len(before_wires) and 20<=len(dirty)<250
removed=[]
for name in sorted(dirty):
 n=b.findNet(name);assert n and str(n.getSigType()) in ["SIGNAL","CLOCK"]
 assert n.getWire() is not None,("missing dirty route",name)
 removed.append({"net":name,"sigtype":str(n.getSigType()),"wire_length_dbu":n.getWire().getLength()})
 odb.dbWire.destroy(n.getWire())
old_obs=len(b.getObstructions())
for p in plans:
 for layer in p["layers"]:assert odb.dbObstruction_create(b,tech.findLayer(layer),*p["box"])
assert len(b.getObstructions())==old_obs+4
retained={n:v for n,v in before_wires.items() if n not in dirty}
assert wires()==retained and cells()==before_cells and graph()==before_graph and pg_shapes()==before_pg
odb.write_db(db,str(partial))
# A separate route-free same-cell/same-graph copy for global-guide regeneration.
for n in b.getNets():
 if n.getWire() is not None:
  assert str(n.getSigType()) not in ["POWER","GROUND"]
  odb.dbWire.destroy(n.getWire())
assert wires()=={} and cells()==before_cells and graph()==before_graph and pg_shapes()==before_pg
odb.write_db(db,str(grt))
assert sha(source)==proof["sha256"]
out={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"source_native_drc":17,"raw_diagnostic":str(rawpath.relative_to(R)),"raw_diagnostic_sha256":sha(rawpath),"pin_feasibility":str(feasibility.relative_to(R)),"pin_feasibility_sha256":sha(feasibility),"codec":str(codec.relative_to(R)),"codec_sha256":sha(codec),"partial":str(partial.relative_to(R)),"partial_sha256":sha(partial),"grt":str(grt.relative_to(R)),"grt_sha256":sha(grt),"plans":plans,"added_routing_obstructions":4,"decoded_regular_wires":decoded,"cleared_whole_nets":removed,"marker_nets":sorted(marker_nets),"keepout_neighborhood_nets":{k:sorted(v) for k,v in intersections.items()},"retained_wire_count":len(retained),"retained_wire_sha256":retained,"unchanged_cells_graph_pg":True,"scope":"Stricter pin-free routing keepouts only; no PDK/LEF/rule change. Clear complete marker nets and all real wire/via shapes within500nm of the layer-specific keepouts, including affected clock net. Preserve all other native wire opcodes/data exactly, with cells, graph and power special wiring unchanged. Separate GRT copy is completely signal/clock-route free. No acceptance; actual regenerated guides, routing, extraction, timing and calibrated independent DRC remain mandatory."}
report.write_text(json.dumps(out,indent=2)+"\n")
assert json.loads(report.read_text())["source_sha256"]==sha(source)
print(json.dumps({k:v for k,v in out.items() if k!="retained_wire_sha256"},indent=2),flush=True)
