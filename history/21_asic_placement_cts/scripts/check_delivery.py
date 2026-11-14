"""Validate the offline handoff and all packaged hashes; no EDA installation needed."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((R/"MANIFEST.sha256.json").read_text())
actual={p.relative_to(R).as_posix() for p in R.rglob("*") if p.is_file() and p.name!="MANIFEST.sha256.json"}
assert actual==set(manifest),("Manifest file set differs",actual^set(manifest))
for name,want in manifest.items():
    assert digest(R/name)==want,("Changed delivery file",name)
for name,want in json.loads((R/"input_identity.json").read_text())["sha256"].items():
    assert digest(R/name)==want,("Frozen input changed",name)
s=json.loads((R/"accepted_summary.json").read_text())
tag=s["run"]
assert s["accepted"] and tag=="placement_release",s
g=json.loads((R/"reports"/tag/"placement_checks.json").read_text())
t=json.loads((R/"reports"/tag/"timing_checks.json").read_text())
assert g["pass"] and g["negative_inversion_fault_detected"] and t["pass"]
assert (g["flip_flops"],g["clock_sink_pins"],g["fixed_macros"],g["signal_pins"])==(2925,2961,18,108)
assert t["max_macro_input_slew_ns"]<=.04000001 and t["active_unannotated_output_drivers"]==0
assert all(s[k]==0 for k in ["slew_violations","cap_violations","power_grid_violations"])
h=json.loads((R/"handoff_state.json").read_text())
assert "spef" not in h, "Routing must not reuse placement-estimated parasitics"
for key,value in h.items():
    if key=="metrics":continue
    prefix="/work/placement_cts/"
    assert isinstance(value,str) and value.startswith(prefix)
    assert (R/value.removeprefix(prefix)).is_file(),(key,value)
assert digest(R/h["nl"].removeprefix("/work/placement_cts/"))==s["netlist_sha256"]==g["netlist_sha256"]
anchors=json.loads((R/"reports/input_driver_anchors.json").read_text())
assert digest(R/"inputs/fault_v_asic_top.odb")==anchors["source_sha256"]
assert digest(R/"inputs/anchored_floorplan.odb")==anchors["derived_sha256"]
assert len(anchors["plans"])==234 and len(anchors["output_plans"])==576
print("ALL OFFLINE DELIVERY / INPUT IDENTITY / ACCEPTED HANDOFF CHECKS PASSED")
