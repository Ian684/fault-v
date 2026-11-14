"""Prepare a final electrical repair using the placed and clocked circuit."""
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
        state[key]="/work/placement_cts/"+paths[0].relative_to(R).as_posix()
assert "odb" in state
(R/f"late_state_{tag}.json").write_text(json.dumps(state,indent=2)+"\n")
physical=json.loads((R/"config.json").read_text())
keys=["DESIGN_NAME","PDK","STD_CELL_LIBRARY","CLOCK_PORT","CLOCK_PERIOD","DEFAULT_CORNER","STA_CORNERS","PNR_CORNERS","PNR_SDC_FILE","SIGNOFF_SDC_FILE","MACROS","VDD_NETS","GND_NETS","PDN_MACRO_CONNECTIONS","RSZ_DONT_TOUCH_RX","STA_EXTRA_CORNER_TCL_FILE"]
cfg={k:physical[k] for k in keys}
cfg.update(meta={"version":2,"flow":["OpenROAD.RepairDesignPostGPL","OpenROAD.STAMidPNR"]},DESIGN_REPAIR_BUFFER_INPUT_PORTS=False,DESIGN_REPAIR_BUFFER_OUTPUT_PORTS=False)
(R/"config_late.json").write_text(json.dumps(cfg,indent=2)+"\n")
print("Prepared post-CTS electrical repair; I/O buffers are retained")
