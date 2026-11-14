"""Resume detailed routing from an independently successful global-route state."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
source,tag=sys.argv[1:3]
assert all(t.replace("_","").isalnum() for t in [source,tag])
state={"metrics":{}}
for key in ["odb","def","nl","pnl","sdc","json_h","vh"]:
    paths=list((R/"runs"/source/"final"/key).glob("*"))
    if paths:
        assert len(paths)==1
        state[key]="/work/routing/"+paths[0].relative_to(R).as_posix()
assert "odb" in state
(R/f"detailed_state_{tag}.json").write_text(json.dumps(state,indent=2)+"\n")
cfg=json.loads((R/"config_global.json").read_text())
cfg["meta"]={"version":2,"flow":["OpenROAD.DetailedRouting","Checker.TrDRC","OpenROAD.CheckAntennas","OpenROAD.RCX"]}
cfg.pop("STA_EXTRA_CORNER_TCL_FILE",None)
cfg.update(DRT_THREADS=8,DRT_OPT_ITERS=64,DRT_ANTENNA_REPAIR_ITERS=0,DRT_SAVE_SNAPSHOTS=True,DRT_SAVE_DRC_REPORT_ITERS=1,ERROR_ON_TR_DRC=True)
(R/"config_detailed.json").write_text(json.dumps(cfg,indent=2)+"\n")
print("Prepared detailed routing and real RC extraction")
