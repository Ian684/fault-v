"""Copy only real zero-overflow guides; keep the same partial-route database."""
from pathlib import Path
import hashlib,json,struct,odb
R=Path("/work/routing")
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=read(R/"reports/cold_corner_keepout_input.json")
source=R/audit["partial"]
global_source=R/"runs/global_cold_corner_keepout/final/odb/fault_v_asic_top.odb"
g=read(R/"reports/global_cold_corner_keepout/global_checks.json")
assert g["pass"] and g["total_overflow"]==0
assert sha(source)==audit["partial_sha256"] and sha(global_source)==g["odb_sha256"]
def load(p):
 d=odb.dbDatabase.create();odb.read_db(d,str(p));return d,d.getChip().getBlock()
d,b=load(source);gd,gb=load(global_source)
def cells(block):
 return {i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation()),str(i.getPlacementStatus())) for i in block.getInsts()}
def graph(block):
 return {n.getName():(str(n.getSigType()),tuple(sorted((t.getInst().getName(),t.getMTerm().getName()) for t in n.getITerms())),tuple(sorted(t.getName() for t in n.getBTerms()))) for n in block.getNets()}
def guide_sig(q):
 via=q.getViaLayer();box=q.getBox()
 return(q.getLayer().getName(),via.getName() if via else q.getLayer().getName(),(box.xMin(),box.yMin(),box.xMax(),box.yMax()),bool(q.isCongested()),bool(q.isConnectedToTerm()),bool(q.isJumper()))
def guides(block):
 return {n.getName():tuple(sorted(guide_sig(q) for q in n.getGuides())) for n in block.getNets()}
def wires(block):
 result={}
 for n in block.getNets():
  w=n.getWire()
  if w is None:continue
  h=hashlib.sha256()
  for j in range(w.length()):h.update(struct.pack("<BI",w.getOpcode(j),w.getData(j)&0xffffffff))
  result[n.getName()]=h.hexdigest()
 return result
before_cells=cells(b);before_graph=graph(b)
assert cells(gb)==before_cells and graph(gb)==before_graph
def obstructions(block):
 return sorted((o.getBBox().getTechLayer().getName(),o.getBBox().xMin(),o.getBBox().yMin(),o.getBBox().xMax(),o.getBBox().yMax()) for o in block.getObstructions())
assert obstructions(b)==obstructions(gb)
access_count=0;term_count=0
for row in audit["cleared_whole_nets"]:
 n=b.findNet(row["net"]);assert n
 for t in n.getITerms():
  aps=t.getPrefAccessPoints();assert aps,("Missing cached AP",t.getInst().getName(),t.getMTerm().getName())
  term_count+=1;x,y=t.getInst().getLocation()
  for ap in aps:
   ax,ay=ap.getPoint();gx,gy=x+ax,y+ay;layer=ap.getLayer().getName()
   assert any(l.getName()==layer and q.xMin()<=gx<=q.xMax() and q.yMin()<=gy<=q.yMax() for l,q in t.getGeometries()),("AP outside actual pin",row["net"],t.getInst().getName(),t.getMTerm().getName())
   access_count+=1
assert access_count>=term_count>0

before_wires=wires(b)
assert before_wires==audit["retained_wire_sha256"]
expected=guides(gb);count=0
for n in b.getNets():
 for q in list(n.getGuides()):odb.dbGuide.destroy(q)
 for layer,via,box,congested,connected,jumper in expected[n.getName()]:
  l=d.getTech().findLayer(layer);v=d.getTech().findLayer(via);assert l and v
  q=odb.dbGuide_create(n,l,v,odb.Rect(*box),congested);assert q
  q.setIsConnectedToTerm(connected);q.setIsJumper(jumper);count+=1
assert guides(b)==expected and cells(b)==before_cells and graph(b)==before_graph
assert wires(b)==before_wires
assert all(expected[n] for n in [x["net"] for x in audit["cleared_whole_nets"]] if before_graph[n][0] not in ["POWER","GROUND"] and len(before_graph[n][1])+len(before_graph[n][2])>=2)
out=R/"inputs/cold_corner_keepout_reguide.odb";assert not out.exists();odb.write_db(d,str(out))
assert sha(source)==audit["partial_sha256"] and sha(global_source)==g["odb_sha256"]
report={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"global_source":str(global_source.relative_to(R)),"global_source_sha256":sha(global_source),"derived":str(out.relative_to(R)),"derived_sha256":sha(out),"guides_copied":count,"retained_wire_count":len(before_wires),"retained_wires_exact_opcode_data_match":True,"cells_and_logical_graph_unchanged":True,"guides_match_actual_zero_overflow_global":True,"cached_access_terminals":term_count,"cached_access_points":access_count,"routing_obstructions_match":True,"scope":"Copy only real zero-overflow guides onto the coherent partially cleared checkpoint. All retained native wire opcodes/data, cells and graph unchanged; stricter routing keepouts match the guide source. Every cached preferred AP on all cleared-net terminals is present and lies in the actual oriented pin geometry. Native routing uses these existing access points; final routing/extraction/actual timing/calibrated independent DRC remain mandatory, no acceptance or wire grafts."}
(R/"reports/cold_corner_reguide_input.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
