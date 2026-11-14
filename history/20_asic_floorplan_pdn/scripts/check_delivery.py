"""Validate the delivered files without running EDA."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/"MANIFEST.json").read_text(encoding="utf-8"))
for name,info in manifest.items():
    p=R/name
    assert p.is_file(), name
    assert p.stat().st_size==info["bytes"], name
    assert hashlib.sha256(p.read_bytes()).hexdigest()==info["sha256"], name
for name,sha in json.loads((R/"input_identity.json").read_text(encoding="utf-8")).items():
    assert hashlib.sha256((R/name).read_bytes()).hexdigest()==sha,name
state=json.loads((R/"handoff_state.json").read_text(encoding="utf-8"))
for key,value in state.items():
    if key=="metrics": continue
    assert value.startswith("/work/floorplan/"), (key,value)
    assert (R/value.removeprefix("/work/floorplan/")).is_file(), (key,value)
for tag in ["floorplan_accepted","floorplan_reproduce"]:
    d=json.loads((R/"reports"/tag/"floorplan_checks.json").read_text(encoding="utf-8"))
    assert d["accepted"] and d["macro_count"]==18 and d["placed_signal_pins"]==108
    assert d["power_grid_violations"]==0 and d["pdn_missing_via_warnings"]==0
    assert d["functional_cell_count"]==29466 and d["functional_iterm_count"]==109529
print(f"ALL {len(manifest)} DELIVERY FILE HASHES / INPUT LOCKS / FLOORPLAN REPORTS PASSED")
