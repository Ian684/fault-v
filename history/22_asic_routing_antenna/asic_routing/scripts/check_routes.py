"""Check routed-wire coverage and export physical wire statistics from OpenDB."""
from pathlib import Path
from collections import Counter
import json,os,hashlib,odb
R=Path(__file__).resolve().parents[1]
tag=os.environ["PLACEMENT_RUN_TAG"]
assert tag.replace("_","").isalnum()
d=odb.dbDatabase.create()
path=R/"runs"/tag/"final/odb/fault_v_asic_top.odb"
odb.read_db(d,str(path))
b=d.getChip().getBlock();u=b.getDbUnitsPerMicron()
active=0;routed=0;missing=[];length=0;layers=Counter();vias=0
geometry=json.loads((R/"reports"/tag/"placement_checks.json").read_text())
clock_nets={b.findBTerm("clk").getNet().getName()}|{b.findInst(n).findITerm("X").getNet().getName() for n in geometry["active_clock_buffer_cells"]}
assert len(clock_nets)==geometry["active_clock_buffer_count"]+1
segments=[]
native_length=0
for net in b.getNets():
    if net.getSigType() in ["POWER","GROUND"]:continue
    pins=[t for t in net.getITerms() if t.getMTerm().getSigType() not in ["POWER","GROUND"]]
    terminals=len(pins)+len(net.getBTerms())
    if terminals<2:continue
    active+=1
    wire=net.getWire()
    if wire is None:missing.append(net.getName());continue
    routed+=1
    native_length+=wire.getLength()/u
    junctions={}
    decoder=odb.dbWireDecoder();decoder.begin(wire)
    layer=None;previous=None
    while True:
        opcode=decoder.next()
        if opcode==decoder.END_DECODE:break
        if opcode==decoder.PATH:
            layer=decoder.getLayer().getName();previous=None
        elif opcode in [decoder.POINT,decoder.POINT_EXT]:
            point=(decoder.getPoint_ext() if opcode==decoder.POINT_EXT else decoder.getPoint())[:2]
            if previous is not None and point!=previous:
                x,y=previous;x2,y2=point
                dist=abs(x2-x)+abs(y2-y)
                length+=dist/u;layers[layer]+=dist/u
                segments.append([layer,x/u,y/u,x2/u,y2/u,net.getName() in clock_nets])
            previous=point
            junctions[decoder.getJunctionId()]=(point,layer)
        elif opcode==decoder.JUNCTION:
            previous,layer=junctions[decoder.getJunctionValue()]
        elif opcode in [decoder.SHORT,decoder.VWIRE]:
            layer=decoder.getLayer().getName();previous=None
        elif opcode in [decoder.TECH_VIA,decoder.VIA]:
            layer=decoder.getLayer().getName();vias+=1
            junctions[decoder.getJunctionId()]=(previous,layer)
assert not missing,("Active nets without routed wires",missing[:30],len(missing))
result={"pass":True,"run":tag,"active_signal_clock_nets":active,"nets_with_wires":routed,"active_nets_missing_wires":missing,"decoded_manhattan_length_um":length,"native_wire_length_um":native_length,"clock_nets":len(clock_nets),"decoded_vias":vias,"length_um_by_layer":dict(layers),"odb_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"scope":"Native length includes endpoint extension effects; decoded length/plot use centerlines. Wire presence plus separate native TritonRoute DRC/connectivity checks, not foundry LVS."}
out=R/"reports"/tag;out.mkdir(exist_ok=True,parents=True)
(out/"route_checks.json").write_text(json.dumps(result,indent=2)+"\n")
(out/"wire_segments.json").write_text(json.dumps(segments)+"\n")
print(json.dumps(result,indent=2))
