"""Accept corrected STA with propagated clocks and placement-estimated parasitics."""
from pathlib import Path
import json,re,sys
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]
assert tag.replace("_","").isalnum()
run=R/"runs"/(tag+"_sta310")
metrics=json.loads((run/"final/metrics.json").read_text())
p=next(run.glob("*-openroad-staprepnr/nom_tt_025C_1v80"))
checks=(p/"checks.rpt").read_text()
setup=(p/"max.rpt").read_text();hold=(p/"min.rpt").read_text()
assert "clkbuf_" in setup and "clkbuf_" in hold, "Missing expanded physical clock paths"
log=(p/"sta.log").read_text()
assert "Reading top-level design parasitics" in log
assert "FAULTV_PROPAGATED_CLOCKS_VERIFIED" in log
geometry=json.loads((R/"reports"/tag/"placement_checks.json").read_text())
match=re.search(r"Found (\d+) unannotated drivers\.\s*\n(.*?)(?:\nFound \d+ partially unannotated drivers\.|\n\s*\n|\Z)",checks,re.S)
assert "Found 0 partially unannotated drivers." in checks, "Partially annotated active RC"
unannotated=[]
if match:
    unannotated=[s.strip().replace("\\","") for s in match[2].splitlines() if s.strip()]
    assert len(unannotated)==int(match[1]),(len(unannotated),match[1])
assert set(unannotated)<=set(geometry["unused_output_driver_pins"]),("Active output has no parasitics",set(unannotated)-set(geometry["unused_output_driver_pins"]))
summary={k:metrics[k] for k in ["timing__setup__ws","timing__hold__ws","timing__setup__tns","timing__hold__tns","timing__setup_vio__count","timing__hold_vio__count","design__max_slew_violation__count","design__max_cap_violation__count","clock__skew__worst_setup","clock__skew__worst_hold"]}
slew_match=re.search(r"FAULTV_MAX_MACRO_INPUT_SLEW_NS ([0-9.eE+-]+) PIN (\S+)",log)
assert slew_match, "Missing explicit constrained SRAM input slew measurement"
summary.update(max_macro_input_slew_ns=float(slew_match[1]),max_macro_input_slew_pin=slew_match[2],engine="OpenSTA 3.1.0",clock_period_ns=40,corner="nom_tt_025C_1v80",parasitics="placement estimated SPEF, not routed extraction",unannotated_unused_output_drivers=len(unannotated),active_unannotated_output_drivers=0)
summary["pass"]=all(summary[k]==0 for k in ["timing__setup__tns","timing__hold__tns","timing__setup_vio__count","timing__hold_vio__count","design__max_slew_violation__count","design__max_cap_violation__count"]) and summary["timing__setup__ws"]>=0 and summary["timing__hold__ws"]>=0
(R/"reports"/tag/"timing_checks.json").write_text(json.dumps(summary,indent=2)+"\n")
print(json.dumps(summary,indent=2))
assert summary["pass"],"Timing or electrical constraints have unresolved violations"
print("ALL CORRECTED POST-CTS ESTIMATED TIMING / SLEW / CAP / ANNOTATION CHECKS PASSED")
