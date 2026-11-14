"""Create a routing handoff only from checked physical and corrected STA results."""
from pathlib import Path
import json,sys,hashlib
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]
assert tag.replace("_","").isalnum()
g=json.loads((R/"reports"/tag/"placement_checks.json").read_text())
t=json.loads((R/"reports"/tag/"timing_checks.json").read_text())
assert g["pass"] and g["negative_inversion_fault_detected"] and g["flip_flops"]==2925 and g["clock_sink_pins"]==2961
assert t["pass"] and t["max_macro_input_slew_ns"]<=.04000001
log=(R.parent/"logs"/(tag+"_physical.log")).read_text()
assert "All shapes on net VPWR are connected." in log and "All shapes on net VGND are connected." in log
assert "ALL POST-CTS PLACEMENT / POWER GRID CHECKS PASSED" in log
for net in ["VPWR","VGND"]:
    p=R/"reports"/tag/(net+"-grid-errors.rpt")
    assert not p.exists() or not p.read_text().strip(),p
state={}
for key in ["odb","def","nl","pnl","sdc","json_h","vh"]:
    paths=list((R/"runs"/tag/"final"/key).glob("*"))
    if paths:
        assert len(paths)==1
        state[key]="/work/placement_cts/"+paths[0].relative_to(R).as_posix()
assert set(["odb","def","nl","pnl","sdc","json_h"])<=set(state)
state["metrics"]={k:v for k,v in t.items() if k.startswith(("timing__","design__","clock__"))}
state["metrics"].update(design__power_grid_violation__count=0)
# Estimated SPEF is an analysis snapshot; routing must estimate/extract new RC.
(R/"handoff_state.json").write_text(json.dumps(state,indent=2)+"\n")
summary={"accepted":True,"run":tag,"netlist_sha256":g["netlist_sha256"],"clock_period_ns":40,"corner":t["corner"],"macro_count":18,"flip_flops":2925,"clock_sink_pins":2961,"active_clock_buffer_count":g["active_clock_buffer_count"],"clock_buffer_depth_range":g["clock_buffer_depth_range"],"instances":g["instances"],"stdcell_area_um2":g["stdcell_area_um2"],"macro_area_um2":g["macro_area_um2"],"setup_ws_ns":t["timing__setup__ws"],"hold_ws_ns":t["timing__hold__ws"],"max_macro_input_slew_ns":t["max_macro_input_slew_ns"],"max_macro_input_slew_pin":t["max_macro_input_slew_pin"],"slew_violations":0,"cap_violations":0,"power_grid_violations":0,"scope":"TT, placement-estimated RC, propagated clocks; no routed extraction or foundry signoff."}
(R/"accepted_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
print("ACCEPTED PLACEMENT / CTS / CORRECTED ESTIMATED TIMING HANDOFF")
print(json.dumps(summary,indent=2))
