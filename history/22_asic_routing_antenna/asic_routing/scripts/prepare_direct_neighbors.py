"""DRC-driven whole-net invalidation for neighboring wires touched by the ECO."""
from pathlib import Path
import hashlib,json,re,struct,odb
R=Path("/work/routing")
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(R/"reports/direct_rc_reguide_input.json")
baseline=read(R/"reports/direct_rc_partial_input.json")
trial=read(R/"reports/direct_rc_trial_preserved.json")
source=R/a["derived"];report=R/trial["report"]
assert sha(source)==a["derived_sha256"] and sha(report)==trial["report_sha256"]
text=report.read_text();assert text.count("violation type:")==1159
names=set(re.findall(r"\bnet:(\S+)",text));assert len(names)==370
d=odb.dbDatabase.create();odb.read_db(d,str(source));b=d.getChip().getBlock()
def cells():return {i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation()),str(i.getPlacementStatus())) for i in b.getInsts()}
def graph():return {n.getName():(str(n.getSigType()),tuple(sorted((t.getInst().getName(),t.getMTerm().getName()) for t in n.getITerms())),tuple(sorted(t.getName() for t in n.getBTerms()))) for n in b.getNets()}
def wires():
 result={}
 for n in b.getNets():
  if n.getSigType() in ["POWER","GROUND"]:continue
  w=n.getWire()
  if w is None:continue
  h=hashlib.sha256()
  for j in range(w.length()):h.update(struct.pack("<BI",w.getOpcode(j),w.getData(j)&0xffffffff))
  result[n.getName()]=h.hexdigest()
 return result
before_cells=cells();before_graph=graph();before_wires=wires()
assert before_wires==baseline["retained_wire_sha256"] and len(before_wires)==40932
removed=[]
for name in sorted(names):
 n=b.findNet(name);assert n is not None,name
 if n.getSigType() in ["POWER","GROUND"]:continue
 if n.getWire() is not None:odb.dbWire.destroy(n.getWire());removed.append(name)
assert len(removed)==275 and all(name in before_wires for name in removed)
expected={k:v for k,v in before_wires.items() if k not in set(removed)}
assert len(expected)==40657 and wires()==expected
assert cells()==before_cells and graph()==before_graph
out=R/"inputs/direct_rc_neighbors.odb";assert not out.exists();odb.write_db(d,str(out))
assert sha(source)==a["derived_sha256"] and sha(report)==trial["report_sha256"]
audit={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"native_drc_report":str(report.relative_to(R)),"native_drc_report_sha256":sha(report),"derived":str(out.relative_to(R)),"derived_sha256":sha(out),"additional_neighbor_wires_removed":removed,"retained_wire_count":40657,"retained_wires_exact_opcode_data_match":True,"cells_and_logical_graph_unchanged":True,"guides_unchanged":True,"scope":"Whole wires of all275 originally retained nets implicated in the actual native DRC trial are invalidated on the untouched baseline partial database. No wires copied from the unsuccessful trial, no placement/clock/logic/gate changes. Fresh native routing and every original acceptance gate required."}
(R/"reports/direct_rc_neighbor_input.json").write_text(json.dumps(audit,indent=2)+"\n")
print(json.dumps({k:v for k,v in audit.items() if k!="additional_neighbor_wires_removed"},indent=2))
