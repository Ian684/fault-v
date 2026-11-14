"""Clear only the nine whole nets in six residual wire crossings; never merge route solutions."""
from pathlib import Path
import odb,json,re,hashlib,struct
R=Path("/work/routing")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/"inputs/residual_source45.odb"
raw=R/"reports/residual_source45.drc.rpt"
assert sha(source)=="d890d384925ac636ab31520c2131ae26fedf84eeeeab78e20a504c86b24b6501"
assert sha(raw)=="99ff40619cad9ea0f43f8f374c93841cbdb4a14aa2ef0a0adad2ccfaaf9c616b"
text=raw.read_text()
assert text.count("violation type:")==6 and set(re.findall(r"violation type:\s*(.+)",text))=={"Short"}
assert "inst:" not in text
names=sorted(set(re.findall(r"net:(\S+)",text)))
assert names==["_09290_","net3183","net3185","net3312","net4951","net4985","net6036","net6166","net6505"]
out=R/"inputs/residual_rc_partial.odb"
report=R/"reports/residual_rc_partial_input.json"
assert not out.exists() and not report.exists()
global_source=R/"runs/global_shrink_rc/final/odb/fault_v_asic_top.odb"
g=json.loads((R/"reports/global_shrink_rc/global_checks.json").read_text())
assert g["pass"] and g["total_overflow"]==0 and sha(global_source)==g["odb_sha256"]
def load(p):
 d=odb.dbDatabase.create();odb.read_db(d,str(p));return d,d.getChip().getBlock()
def cells(b):
 return {i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation()),str(i.getPlacementStatus())) for i in b.getInsts()}
def graph(b):
 return {n.getName():(str(n.getSigType()),tuple(sorted((t.getInst().getName(),t.getMTerm().getName()) for t in n.getITerms())),tuple(sorted(t.getName() for t in n.getBTerms()))) for n in b.getNets()}
def wires(b):
 result={}
 for n in b.getNets():
  w=n.getWire()
  if w is None:continue
  h=hashlib.sha256()
  for j in range(w.length()):h.update(struct.pack("<BI",w.getOpcode(j),w.getData(j)&0xffffffff))
  result[n.getName()]=h.hexdigest()
 return result
def guide_sig(q):
 v=q.getViaLayer();r=q.getBox()
 return (q.getLayer().getName(),v.getName() if v else q.getLayer().getName(),(r.xMin(),r.yMin(),r.xMax(),r.yMax()),bool(q.isCongested()),bool(q.isConnectedToTerm()),bool(q.isJumper()))
d,b=load(source);gd,gb=load(global_source)
before_cells=cells(b);before_graph=graph(b);before_wires=wires(b)
assert cells(gb)==before_cells and graph(gb)==before_graph
assert len(before_wires)==41331
for name in names:
 n=b.findNet(name);assert n and n.getWire() and str(n.getSigType()) not in ["POWER","GROUND"]
 assert len(list(n.getITerms()))+len(list(n.getBTerms()))>=2
 odb.dbWire.destroy(n.getWire())
expected={n:h for n,h in before_wires.items() if n not in names}
count=0
for n in b.getNets():
 for q in list(n.getGuides()):odb.dbGuide.destroy(q)
 gn=gb.findNet(n.getName());assert gn
 sig=sorted(guide_sig(q) for q in gn.getGuides())
 for layer,via,box,congested,connected,jumper in sig:
  q=odb.dbGuide_create(n,d.getTech().findLayer(layer),d.getTech().findLayer(via),odb.Rect(*box),congested)
  assert q
  q.setIsConnectedToTerm(connected);q.setIsJumper(jumper);count+=1
 assert sorted(guide_sig(q) for q in n.getGuides())==sig
assert all(list(b.findNet(n).getGuides()) for n in names)
assert cells(b)==before_cells and graph(b)==before_graph and wires(b)==expected
assert len(expected)==41322
odb.write_db(d,str(out))
assert sha(source)=="d890d384925ac636ab31520c2131ae26fedf84eeeeab78e20a504c86b24b6501"
assert sha(global_source)==g["odb_sha256"]
result={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"source_native_markers":6,"source_drc":str(raw.relative_to(R)),"source_drc_sha256":sha(raw),"global_source":str(global_source.relative_to(R)),"global_source_sha256":sha(global_source),"derived":str(out.relative_to(R)),"derived_sha256":sha(out),"cleared_whole_nets":names,"cleared_wire_count":9,"retained_wire_count":len(expected),"retained_wire_sha256":expected,"guides_copied":count,"cells_and_graph_match_zero_overflow_global":True,"retained_wires_exact_opcode_data_match":True,"scope":"One coherent saved native checkpoint with six unresolved shorts. Clear the nine complete signal wires only; no moved/resized cells, no wire grafts, no acceptance. Copy only zero-overflow guides from the exact same cell/graph parent. Fresh native routing, extraction, actual STA and independent DRC remain required."}
report.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="retained_wire_sha256"},indent=2))
