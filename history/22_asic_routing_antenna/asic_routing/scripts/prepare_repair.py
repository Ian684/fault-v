"""Repair the globally routed electrical network before spending time on detailed routing."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
source,tag=sys.argv[1:3]
mode=sys.argv[3] if len(sys.argv)>3 else "full"
assert mode in ["full","electrical"]
assert all(t.replace("_","").isalnum() for t in [source,tag])
state={"metrics":{}}
for key in ["odb","def","nl","pnl","sdc","json_h","vh"]:
    files=list((R/"runs"/source/"final"/key).glob("*"))
    if files:
        assert len(files)==1
        state[key]="/work/routing/"+files[0].relative_to(R).as_posix()
assert "odb" in state
(R/f"repair_state_{tag}.json").write_text(json.dumps(state,indent=2)+"\n")
cfg=json.loads((R/"config_global.json").read_text())
cfg["meta"]={"version":2,"flow":["OpenROAD.RepairDesignPostGRT","OpenROAD.ResizerTimingPostGRT","OpenROAD.STAMidPNR"]}
cfg.update(GRT_DESIGN_REPAIR_MAX_WIRE_LENGTH=500,GRT_DESIGN_REPAIR_MAX_SLEW_PCT=30,GRT_DESIGN_REPAIR_MAX_CAP_PCT=30,GRT_RESIZER_HOLD_SLACK_MARGIN=0.3,GRT_RESIZER_SETUP_GATE_CLONING=False,PL_OPTIMIZE_MIRRORING=False)
if mode=="electrical":
    cfg["meta"]["flow"]=["OpenROAD.RepairDesignPostGRT","OpenROAD.STAMidPNR"]
    cfg["PL_OPTIMIZE_MIRRORING"]=False
(R/"config_repair.json").write_text(json.dumps(cfg,indent=2)+"\n")
print("Prepared global-route electrical/hold repair with unchanged SDC")
