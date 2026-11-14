"""Clear the complete data-net neighborhood of five crossings in one coherent database."""
from pathlib import Path
import odb,json,re,hashlib,struct
R=Path("/work/routing")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/"reports/residual_geometry26_source.odb"
raw=R/"reports/residual_geometry26.drc.rpt"
assert sha(source)=="fc748ae797cffc8e786019c824537c86451a0a604d3a2789945153626a36fc5c"
assert sha(raw)=="45ff072803dafb3d688e090647eed5b6c182b82b4a343c4d505eef4db1236529"
text=raw.read_text()
assert text.count("violation type:")==5 and set(re.findall(r"violation type:\s*(.+)",text))=={"Short"}
assert "inst:" not in text
geometry_path=R/"reports/residual_corner_shapes.json"
classes_path=R/"reports/residual_corner_neighbor_classes.json"
geometry=json.loads(geometry_path.read_text());classes=json.loads(classes_path.read_text())
assert geometry["source_sha256"]==classes["source_sha256"]==sha(source)
assert tuple(geometry["region"])==(1580000,633000,1589000,643000)
names=sorted({q[-1] for q in geometry["shapes"] if q[0] in ["met1","met2","met3","met4","met5"] and q[-1] not in ["@obs","VPWR","VGND","@pin"]})
assert len(names)==56 and names==sorted(r["net"] for r in classes["nets"])
assert set(re.findall(r"net:(\S+)",text))<=set(names)
assert all(r["sigtype"]=="SIGNAL" and r["terminals"]>=2 and r["has_wire"] and not r["protected_sram_cells"] for r in classes["nets"])
out=R/"inputs/neighborhood_rc_partial.odb"
report=R/"reports/neighborhood_rc_partial_input.json"
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
 n=b.findNet(name);assert n and n.getWire() and str(n.getSigType())=="SIGNAL"
 assert len(list(n.getITerms()))+len(list(n.getBTerms()))>=2
 assert not any(re.fullmatch(r"eco_sram_(n[0-9]+_.*|b[0-9]+_(first|last))|sram_out_iso_.*",t.getInst().getName()) for t in n.getITerms())
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
assert len(expected)==41275
odb.write_db(d,str(out))
assert sha(source)=="fc748ae797cffc8e786019c824537c86451a0a604d3a2789945153626a36fc5c"
assert sha(global_source)==g["odb_sha256"]
result={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"source_native_markers":5,"source_drc":str(raw.relative_to(R)),"source_drc_sha256":sha(raw),"global_source":str(global_source.relative_to(R)),"global_source_sha256":sha(global_source),"derived":str(out.relative_to(R)),"derived_sha256":sha(out),"neighborhood_geometry":str(geometry_path.relative_to(R)),"neighborhood_geometry_sha256":sha(geometry_path),"neighborhood_classes":str(classes_path.relative_to(R)),"neighborhood_classes_sha256":sha(classes_path),"selection_region_dbu":geometry["region"],"cleared_clock_or_protected_sram_nets":0,"cleared_whole_nets":names,"cleared_wire_count":56,"retained_wire_count":len(expected),"retained_wire_sha256":expected,"guides_copied":count,"cells_and_graph_match_zero_overflow_global":True,"retained_wires_exact_opcode_data_match":True,"scope":"One coherent native checkpoint26 with five real polygon overlaps. Clear the complete 56-active-data-net neighborhood selected from actual metal/via/pin polygons in a 9x10um region. No clock or protected SRAM chain net is selected; verified again on the source database. No moved/resized cells, no wire grafts or acceptance. All 41275 remaining regular wires must match exact opcodes/data; guides only come from the same-cell/same-graph zero-overflow global parent. Fresh native routing/extraction/actual STA/independent DRC remain mandatory."}
report.write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="retained_wire_sha256"},indent=2))
