"""Use standard clock routing rules, preserving clock topology and electrical SDC."""
from pathlib import Path
import odb,json,hashlib
R=Path(__file__).resolve().parents[1]
src=R/"inputs/fault_v_asic_top.odb"
d=odb.dbDatabase.create();odb.read_db(d,str(src))
b=d.getChip().getBlock()
queue=[b.findBTerm("clk").getNet()];clock_nets=set()
while queue:
    net=queue.pop()
    assert net.getName() not in clock_nets
    clock_nets.add(net.getName())
    for pin in net.getITerms():
        if pin.getIoType()!="INPUT":continue
        i=pin.getInst();m=i.getMaster().getName()
        if m.startswith(("sky130_fd_sc_hd__clkbuf_","sky130_fd_sc_hd__buf_","sky130_fd_sc_hd__clkdlybuf")):
            out=i.findITerm("X")
            assert out
            nxt=out.getNet()
            if nxt and any(t.getIoType()=="INPUT" for t in nxt.getITerms()):queue.append(nxt)
changes=[]
for net in b.getNets():
    rule=net.getNonDefaultRule()
    if rule:
        assert net.getName() in clock_nets,("Unexpected data NDR",net.getName())
        changes.append({"net":net.getName(),"old_rule":rule.getName()})
        net.setNonDefaultRule(None)
assert changes
target=R/"inputs/standard_clock_rules.odb"
odb.write_db(d,str(target))
report={"clock_network_nets":len(clock_nets),"cleared_clock_ndrs":len(changes),"changes":changes,"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"derived_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),"scope":"Only net non-default routing-rule assignments removed; no cells, pins, logical connections or SDC changed."}
(R/"reports/clock_routing_rules.json").write_text(json.dumps(report,indent=2)+"\n")
state=json.loads((R/"initial_state_original.json").read_text())
state["odb"]="/work/routing/inputs/standard_clock_rules.odb"
state.pop("def",None)
(R/"initial_state.json").write_text(json.dumps(state,indent=2)+"\n")
print(json.dumps({k:v for k,v in report.items() if k!="changes"},indent=2))
