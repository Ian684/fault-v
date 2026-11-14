from pathlib import Path
import odb,hashlib,json,shutil
R=Path("/work/routing");source=R/"runs/global_followup_rc/final/odb/fault_v_asic_top.odb"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=="041bec076075968f3f84569d6580d280f76bed647d89400ef358ffbb12ae6cd6"
g=json.loads((R/"reports/global_followup_rc/global_checks.json").read_text())
a=json.loads((R/"reports/followup_rc_reguide_input.json").read_text())
assert g["pass"] and g["total_overflow"]==0 and a["global_source_sha256"]==sha(source) and a["cells_and_logical_graph_unchanged"]
d=odb.dbDatabase.create();odb.read_db(d,str(source));b=d.getChip().getBlock()
wires=[n.getName() for n in b.getNets() if str(n.getSigType()) not in ["POWER","GROUND"] and n.getWire()]
guides=sum(len(n.getGuides()) for n in b.getNets())
assert not wires,wires
assert guides==373252,guides
out=R/"inputs/followup_cold_global.odb";assert not out.exists();shutil.copyfile(source,out);assert sha(out)==sha(source)
record={"accepted":False,"source":source.relative_to(R).as_posix(),"source_sha256":sha(source),"input":out.relative_to(R).as_posix(),"input_sha256":sha(out),"signal_clock_detailed_wires":len(wires),"guides":guides,"same_cells_graph_proof":"reports/followup_rc_reguide_input.json","same_cells_graph_verified":True,"global_overflow":0,"scope":"Full coherent route-free zerooverflow global source for standard freshPA/native normal detailed routing. No retained old detailed routes or cross-solution splicing; actual RC/timing/independentDRC still required."}
(R/"reports/followup_cold_input.json").write_text(json.dumps(record,indent=2)+"\n");print(json.dumps(record,indent=2))
