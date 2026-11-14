from pathlib import Path
import hashlib,json,odb
R=Path("/work/routing")
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old_audit=read(R/"reports/pin_spread_s0_input.json")
first_audit=read(R/"reports/pin_spread_input.json")
source=R/"inputs/route_pin_spread_s0.odb"
global_source=R/"runs/global_pin_spread/final/odb/fault_v_asic_top.odb"
global_checks=read(R/"reports/global_pin_spread/global_checks.json")
assert global_checks["pass"] and global_checks["total_overflow"]==0
assert read(R/"reports/global_pin_spread/timing_checks.json")["pass"]
assert sha(source)==old_audit["derived_sha256"] and sha(global_source)==global_checks["odb_sha256"]
names={x["net"] for x in first_audit["ripped_nets"]+old_audit["ripped_nets"]}
assert len(names)==20
d=odb.dbDatabase.create();odb.read_db(d,str(source));b=d.getChip().getBlock()
gd=odb.dbDatabase.create();odb.read_db(gd,str(global_source));gb=gd.getChip().getBlock()
def cells(block):
 return {i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation()),str(i.getPlacementStatus())) for i in block.getInsts()}
def graph(block):
 return {n.getName():(str(n.getSigType()),tuple(sorted((t.getInst().getName(),t.getMTerm().getName()) for t in n.getITerms())),tuple(sorted(t.getName() for t in n.getBTerms()))) for n in block.getNets()}
def guide_sig(q):
 via=q.getViaLayer()
 box=q.getBox()
 return(q.getLayer().getName(),via.getName() if via else q.getLayer().getName(),(box.xMin(),box.yMin(),box.xMax(),box.yMax()),bool(q.isCongested()),bool(q.isConnectedToTerm()),bool(q.isJumper()))
def guide_map(block):
 return {n.getName():tuple(sorted(guide_sig(q) for q in n.getGuides())) for n in block.getNets()}
before_cells=cells(b);before_graph=graph(b)
assert cells(gb)==before_cells and graph(gb)==before_graph
before_wires={n.getName():n.getWire().getLength() for n in b.getNets() if n.getWire()}
assert len(before_wires)==41294
assert all(b.findNet(name) and not b.findNet(name).getWire() for name in names)
expected=guide_map(gb);count=0
for n in b.getNets():
 for q in list(n.getGuides()):odb.dbGuide.destroy(q)
 for layer,via,box,congested,connected,jumper in expected[n.getName()]:
  l=d.getTech().findLayer(layer);v=d.getTech().findLayer(via);assert l and v
  q=odb.dbGuide_create(n,l,v,odb.Rect(*box),congested);assert q
  q.setIsConnectedToTerm(connected);q.setIsJumper(jumper);count+=1
assert guide_map(b)==expected
assert cells(b)==before_cells and graph(b)==before_graph
assert {n.getName():n.getWire().getLength() for n in b.getNets() if n.getWire()}==before_wires
assert all(expected[name] for name in names)
after={n.getName():n.getWire().getLength() for n in b.getNets() if n.getWire()}
assert after==before_wires and len(after)==41294
assert cells(b)==before_cells and graph(b)==before_graph
out=R/"inputs/pin_spread_reguide.odb";assert not out.exists();odb.write_db(d,str(out))
assert sha(source)==old_audit["derived_sha256"] and sha(global_source)==global_checks["odb_sha256"]
audit={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"global_source":str(global_source.relative_to(R)),"global_source_sha256":sha(global_source),"derived":str(out.relative_to(R)),"derived_sha256":sha(out),"unrouted_nets":sorted(names),"retained_wire_count":len(after),"guides_copied":count,"guides_match_new_global":True,"cells_and_logical_graph_unchanged":True,"other_wire_lengths_unchanged":True,"physical_obstructions_added":0,"scope":"Use previously verified three-cell ECO partial route (20 signal nets already removed), replace all guides with the actual zero-overflow/estimated-electrical-pass global_pin_spread guides, preserve other41294wire lengths and exact cell/logic identity. Fresh native PA and normal main, then all original extracted/independent acceptance gates required."}
(R/"reports/pin_spread_reguide_input.json").write_text(json.dumps(audit,indent=2)+"\n")
print(json.dumps(audit,indent=2))
