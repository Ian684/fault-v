"""Fail before implementation if frozen design, runtime or selected PDK inputs differ."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
lock=json.loads((R/"input_identity.json").read_text())
for name,digest in lock["sha256"].items():
    assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,("Changed input",name)
technology=json.loads((R/"technology_identity.json").read_text())
for name,digest in technology["selected_pdk_files"].items():
    assert hashlib.sha256((R.parent/"pdk"/name).read_bytes()).hexdigest()==digest,("Changed PDK file",name)
print("ALL FROZEN INPUT / RUNTIME / SELECTED PDK HASH CHECKS PASSED")
