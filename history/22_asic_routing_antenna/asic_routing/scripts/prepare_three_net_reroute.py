from pathlib import Path
import odb,json,hashlib
R=Path("/work/routing")
source=R/"runs/routed_final/1-openroad-detailedrouting/drt_iter52.odb"
out=R/"inputs/three_net_reroute.odb"
audit=R/"reports/three_net_reroute_input.json"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected="d76e62334708948ae6ef721082b11bf4f929c410084d83032dae5e828cf155a7"
assert sha(source)==expected and not out.exists() and not audit.exists()
cal=json.loads((R/"reports/drc_gate_negative/full_drc_calibration.json").read_text())
assert cal["odb_sha256"]==expected and cal["unresolved_count"]==2
d=odb.dbDatabase.create();odb.read_db(d,str(source));b=d.getChip().getBlock()
def identity():
    cells=sorted((i.getName(),i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation()),str(i.getPlacementStatus())) for i in b.getInsts())
    graph=sorted((n.getName(),str(n.getSigType()),sorted((p.getInst().getName(),p.getMTerm().getName()) for p in n.getITerms()),sorted(p.getName() for p in n.getBTerms())) for n in b.getNets())
    return hashlib.sha256(json.dumps([cells,graph],separators=(",",":")).encode()).hexdigest()
before_identity=identity()
before_wires={n.getName():n.getWire().getLength() for n in b.getNets() if n.getWire()}
names=sorted({name.removeprefix("net:") for marker in cal["unresolved"] for name in marker["srcs"].split()})
names=[name for name in names if b.findNet(name).getSigType() not in ["POWER","GROUND"]]
assert names==["_03553_","_10901_","net2689"],names
removed=[]
for name in names:
    n=b.findNet(name);assert n and n.getWire()
    assert len(n.getGuides())>0,("Original guides required",name)
    removed.append({"net":name,"wire_length_dbu":n.getWire().getLength(),"guides":len(n.getGuides())})
    odb.dbWire_destroy(n.getWire())
after_wires={n.getName():n.getWire().getLength() for n in b.getNets() if n.getWire()}
assert after_wires=={name:length for name,length in before_wires.items() if name not in names}
assert identity()==before_identity
odb.write_db(d,str(out))
assert sha(source)==expected
record={"accepted":False,"source":source.relative_to(R).as_posix(),"source_sha256":expected,"derived":out.relative_to(R).as_posix(),"derived_sha256":sha(out),"removed_nets":removed,"retained_wires":len(after_wires),"cells_and_logical_graph_sha256":before_identity,"cells_and_logical_graph_unchanged":True,"other_wire_lengths_unchanged":True,"original_guides_retained":True,"scope":"Only the three signal nets identified by two calibrated true shorts are removed in a new ODB. No cell, master, pin, guide, routing rule, PG or calibration changes. Native fresh pin-access and normal main routing, then all original acceptance gates required."}
audit.write_text(json.dumps(record,indent=2)+"\n")
print(json.dumps(record,indent=2))
