"""Check frozen implementation inputs and the used PDK/model files before routing."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,digest in json.loads((R/"input_identity.json").read_text())["sha256"].items():
    assert sha(R/name)==digest,("Changed input",name)
for name,digest in json.loads((R/"technology_identity.json").read_text())["selected_pdk_files"].items():
    assert sha(R.parent/"pdk"/name)==digest,("Changed PDK/model",name)
print("ALL FROZEN ROUTING INPUT / TOOL / PDK HASH CHECKS PASSED")
