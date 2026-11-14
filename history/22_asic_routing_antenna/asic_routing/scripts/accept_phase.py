"""Promote only a routed, extracted and electrically checked design to handoff."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
global_tag,tag=sys.argv[1:3]
assert all(t.replace("_","").isalnum() for t in [global_tag,tag])
read=lambda p:json.loads(p.read_text(encoding="utf-8"))
g=read(R/"reports"/tag/"placement_checks.json")
w=read(R/"reports"/tag/"route_checks.json")
t=read(R/"reports"/tag/"timing_checks.json")
gr=read(R/"reports"/global_tag/"global_checks.json")
source=read(R/"reports"/f"{tag}_sta_source.json")
independent_drc=read(R/"reports"/tag/"full_drc_checks.json")
assert independent_drc["pass"] and independent_drc["independent_full_chip_drc"]==0 and independent_drc["negative_control_known_shorts"]==2
assert independent_drc["odb_sha256"]==w["odb_sha256"]
assert independent_drc["raw_marker_count"]==independent_drc["confirmed_partition_artifacts"]+independent_drc["independent_full_chip_drc"]
m=read(R/"runs"/tag/"final/metrics.json")
assert gr["pass"] and gr["total_overflow"]==0
assert g["pass"] and g["negative_inversion_fault_detected"]
assert w["pass"] and not w["active_nets_missing_wires"]
assert t["pass"] and t["max_macro_input_slew_ns"]<=.04000001 and source["scope"]=="routed"
assert g["flip_flops"]==2925 and g["clock_sink_pins"]==2961
assert m["route__drc_errors"]==0,m.get("route__drc_errors")
log=(R.parent/"logs"/f"{tag}_physical.log").read_text(encoding="utf-8")
assert all(s in log for s in ["All shapes on net VPWR are connected.","All shapes on net VGND are connected.","ALL POST-CTS PLACEMENT / POWER GRID CHECKS PASSED"])
state={}
final=R/"runs"/tag/"final"
for key in ["odb","def","nl","pnl","sdc","json_h","vh"]:
    files=list((final/key).glob("*"))
    if files:
        assert len(files)==1
        state[key]="/work/routing/"+files[0].relative_to(R).as_posix()
assert {"odb","def","nl","pnl","sdc","json_h"}<=set(state)
spefs=list((final/"spef").rglob("*.spef"))
assert len(spefs)==3
state["spef"]={}
for corner in ["nom","min","max"]:
    files=[p for p in spefs if corner in p.name]
    assert len(files)==1,(corner,files)
    state["spef"][corner+"_*"]="/work/routing/"+files[0].relative_to(R).as_posix()
state["metrics"]={k:v for k,v in t.items() if k.startswith(("timing__","design__","clock__"))}
state["metrics"].update(route__drc_errors=0,design__power_grid_violation__count=0)
antenna=int(m["route__antenna_violation__count"])
assert antenna>=0,"Missing valid antenna report"
state["metrics"]["route__antenna_violation__count"]=antenna
summary={"accepted":True,"global_run":global_tag,"routed_run":tag,"clock_period_ns":40,"corner":"nom_tt_025C_1v80","parasitics":"OpenRCX extracted nominal routed SPEF","global_overflow":0,"routing_drc":0,"setup_ws_ns":t["timing__setup__ws"],"hold_ws_ns":t["timing__hold__ws"],"max_macro_input_slew_ns":t["max_macro_input_slew_ns"],"slew_violations":0,"cap_violations":0,"active_signal_clock_nets":w["active_signal_clock_nets"],"wire_length_um":w["native_wire_length_um"],"vias":w["decoded_vias"],"flip_flops":2925,"clock_sink_pins":2961,"macro_count":18,"netlist_sha256":g["netlist_sha256"],"odb_sha256":w["odb_sha256"],"reported_antenna_nets":antenna,"scope":"Routing-stage acceptance only: TT timing and router-supported LEF rules. Full foundry DRC/LVS, antenna closure, multiple PVT and physical signoff remain."}
(R/"handoff_state.json").write_text(json.dumps(state,indent=2)+"\n")
(R/"accepted_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("ACCEPTED ROUTED / EXTRACTED / TT TIMING HANDOFF")
print(json.dumps(summary,indent=2))
