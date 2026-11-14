from pathlib import Path
import odb,json,hashlib
R=Path("/work/routing");source=R/"runs/global_buffered/final/odb/fault_v_asic_top.odb"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=="51f9f4d21395b68ad460a7be3076dadfea16d5c6dcadee913e4b0dda52516052"
d=odb.dbDatabase.create();odb.read_db(d,str(source));b=d.getChip().getBlock()
roi=(1580100,634800,1593900,648600)
rect=lambda q:(q.xMin(),q.yMin(),q.xMax(),q.yMax())
hit=lambda q:q[0]<roi[2] and q[2]>roi[0] and q[1]<roi[3] and q[3]>roi[1]
pins=[]
for i in b.getInsts():
 if not hit(rect(i.getBBox())):continue
 for it in i.getITerms():
  if str(it.getSigType()) in ["POWER","GROUND"]:continue
  for layer,q in it.getGeometries():
   if hit(rect(q)):pins.append({"cell":i.getName(),"pin":it.getMTerm().getName(),"layer":layer.getName(),"bbox":rect(q)})
for it in b.getBTerms():
 if str(it.getSigType()) in ["POWER","GROUND"]:continue
 for bp in it.getBPins():
  for q in bp.getBoxes():
   if hit(rect(q)):pins.append({"bterm":it.getName(),"bbox":rect(q)})
wires=sum(bool(n.getWire()) for n in b.getNets() if str(n.getSigType()) not in ["POWER","GROUND"])
audit={"accepted":False,"source":str(source.relative_to(R)),"source_sha256":sha(source),"region_dbu":roi,"layers":["met1","met2","met3","met4"],"capacity_reduction":1.0,"nonpower_pins_in_region":pins,"source_signal_clock_wire_count":wires,"scope":"Coarse-routing capacity reservation only at one pinless SRAM corner across2x2 GCells; no physical obstructions, cell/PG/pin/logic/SDC changes. Final DRT/RC/independentDRC gates remain required."}
(R/"reports/corner_reserve_input.json").write_text(json.dumps(audit,indent=2)+"\n");print(json.dumps(audit,indent=2))
assert not pins and wires==0,(pins,wires)
