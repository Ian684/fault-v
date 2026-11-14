"""Fix existing two-stage SRAM input drivers close to macro pins on legal rows."""
from pathlib import Path
from collections import defaultdict
import json,hashlib
import odb
R=Path(__file__).resolve().parents[1]
src=R/"inputs/fault_v_asic_top.odb"
db=odb.dbDatabase.create();odb.read_db(db,str(src));b=db.getChip().getBlock()
rows=[];occupied=defaultdict(list)
for i in b.getInsts():
    if i.isFixed() and i.getMaster().getType()!="BLOCK":
        q=i.getBBox();occupied[q.yMin()].append((q.xMin(),q.xMax()))
for row in b.getRows():
    q=row.getBBox();free=[(q.xMin(),q.xMax())]
    for lo,hi in sorted(occupied[q.yMin()]):
        free=[v for a,c in free for v in [(a,min(lo,c)),(max(hi,a),c)] if v[1]>v[0]] if any(a<hi and lo<c for a,c in free) else free
    rows.append({"y":q.yMin(),"lo":q.xMin(),"hi":q.xMax(),"orient":row.getOrient(),"free":free})
def locate(i, pin, target):
    w=i.getMaster().getWidth();best=None
    offsets={}
    for orient in ["R0","MX"]:
        i.setOrient(orient);i.setLocation(0,0)
        ok,x,y=i.findITerm(pin).getAvgXY();assert ok
        offsets[orient]=(x,y)
    for row in rows:
        y=row["y"];o=str(row["orient"])
        assert o in offsets,o
        dx,dy=offsets[o]
        if abs(y+dy-target[1])>80000:continue
        for lo,hi in row["free"]:
            if hi-lo<w:continue
            lower=((lo+459)//460)*460
            upper=((hi-w)//460)*460
            if lower>upper:continue
            x=min(upper,max(lower,round((target[0]-dx)/460)*460))
            score=abs(x+dx-target[0])+abs(y+dy-target[1])
            if best is None or score<best[0]:best=(score,row,lo,hi,x)
    assert best is not None,(i.getName(),target,w)
    score,row,lo,hi,x=best
    row["free"].remove((lo,hi))
    for a,c in [(lo,x),(x+w,hi)]:
        if c>a:row["free"].append((a,c))
    i.setOrient(row["orient"]);i.setLocation(x,row["y"]);i.setPlacementStatus("FIRM")
    return {"instance":i.getName(),"location_um":[x/1000,row["y"]/1000],"orientation":str(row["orient"]),"pin_manhattan_um":score/1000}
def replace_pair_cell(old, master_name):
    name=old.getName()
    nets={t.getMTerm().getName():t.getNet() for t in old.getITerms()}
    assert nets["A"] and nets["X"]
    odb.dbInst_destroy(old)
    inst=odb.dbInst_create(b,db.findMaster(master_name),name)
    inst.findITerm("A").connect(nets["A"])
    inst.findITerm("Y").connect(nets["X"])
    for pin in ["VPWR","VGND","VPB","VNB"]:
        inst.findITerm(pin).connect(nets[pin])
    return inst
plans=[];targets=set()
for n in range(234):
    last=b.findInst(f"eco_sram_b{n}_last");first=b.findInst(f"eco_sram_b{n}_first")
    assert last and first
    assert last.getMaster().getName()=="sky130_fd_sc_hd__buf_16"
    assert first.getMaster().getName()=="sky130_fd_sc_hd__buf_4"
    last=replace_pair_cell(last,"sky130_fd_sc_hd__inv_16")
    first=replace_pair_cell(first,"sky130_fd_sc_hd__inv_16")
    pins=[t for t in last.findITerm("Y").getNet().getITerms() if t.getInst().getMaster().getType()=="BLOCK"]
    assert len(pins)==1
    t=pins[0];assert t.getMTerm().getName().startswith(("addr0[","wmask0["))
    targets.add((t.getInst().getName(),t.getMTerm().getName()))
    ok,x,y=t.getAvgXY();assert ok
    lp=locate(last,"Y",(x,y))
    ok,x,y=last.findITerm("A").getAvgXY();assert ok
    fp=locate(first,"Y",(x,y))
    source=first.findITerm("A").getNet()
    local=odb.dbNet_create(b,f"eco_sram_n{n}_shape")
    pre=odb.dbInst_create(b,db.findMaster("sky130_fd_sc_hd__buf_4"),f"eco_sram_b{n}_shape")
    first.findITerm("A").disconnect();first.findITerm("A").connect(local)
    pre.findITerm("A").connect(source);pre.findITerm("X").connect(local)
    for p in pre.getITerms():
        st=p.getMTerm().getSigType()
        if st in ["POWER","GROUND"]:p.connect(b.findNet("VPWR" if st=="POWER" else "VGND"))
    ok,x,y=first.findITerm("A").getAvgXY();assert ok
    pp=locate(pre,"X",(x,y))
    plans.append({"macro":t.getInst().getName(),"pin":t.getMTerm().getName(),"last":lp,"first":fp,"shaper":pp})
assert len(targets)==234
output_plans=[]
macros=[i for i in b.getInsts() if i.getMaster().getType()=="BLOCK"]
for bank,macro in enumerate(macros):
    for bit in range(32):
        pin=macro.findITerm(f"dout0[{bit}]")
        net=pin.getNet()
        assert net is not None,(macro.getName(),bit)
        ok,x,y=pin.getAvgXY();assert ok
        inst=odb.dbInst_create(b,db.findMaster("sky130_fd_sc_hd__buf_4"),f"sram_out_iso_b{bank}_{bit}")
        local=odb.dbNet_create(b,f"sram_out_iso_n{bank}_{bit}")
        pin.disconnect();pin.connect(local)
        inst.findITerm("A").connect(local)
        inst.findITerm("X").connect(net)
        for t in inst.getITerms():
            st=t.getMTerm().getSigType()
            if st in ["POWER","GROUND"]:t.connect(b.findNet("VPWR" if st=="POWER" else "VGND"))
        pos=locate(inst,"A",(x,y))
        output_plans.append({"macro":macro.getName(),"pin":pin.getMTerm().getName(),"buffer":pos})
assert len(output_plans)==576
out=R/"inputs/anchored_floorplan.odb"
odb.write_db(db,str(out))
(R/"reports/input_driver_anchors.json").write_text(json.dumps({"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"derived_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),"input_chain":"buf_4 -> inv_16 -> inv_16","added_input_shapers":234,"relocated_input_cells":468,"added_readout_buffers":576,"max_readout_pin_manhattan_um":max(p["buffer"]["pin_manhattan_um"] for p in output_plans),"output_plans":output_plans,"max_last_pin_manhattan_um":max(p["last"]["pin_manhattan_um"] for p in plans),"max_interstage_manhattan_um":max(p["first"]["pin_manhattan_um"] for p in plans),"plans":plans},indent=2)+"\n")
print("Anchored 234 shaped positive input chains and 576 readout isolation buffers; no architectural state change")
