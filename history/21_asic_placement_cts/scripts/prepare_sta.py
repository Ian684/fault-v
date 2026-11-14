"""Build standalone STA inputs from the final placed/CTS database export."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]
assert tag.replace("_","").isalnum(),tag
run=R/"runs"/tag
spefs=sorted(run.glob("*-openroad-stamidpnr*/estimated.spef"),key=lambda p:int(p.parent.name.split("-")[0]))[-1:]
assert len(spefs)==1 and spefs[0].stat().st_size>100000, spefs
base="/work/placement_cts/"
state={"nl":base+str((run/"final/nl/fault_v_asic_top.nl.v").relative_to(R)),
       "spef":{"nom_tt_025C_1v80":base+str(spefs[0].relative_to(R))},"metrics":{}}
(R/f"sta_state_{tag}.json").write_text(json.dumps(state,indent=2)+"\n")
physical_cfg=json.loads((R/"config.json").read_text())
cfg={k:physical_cfg[k] for k in ["DESIGN_NAME","PDK","STD_CELL_LIBRARY","CLOCK_PORT","CLOCK_PERIOD","DEFAULT_CORNER","STA_CORNERS","PNR_SDC_FILE","SIGNOFF_SDC_FILE","MACROS"]}
cfg["meta"]={"version":2,"flow":["OpenROAD.STAPrePNR"]}
cfg["STA_EXTRA_CORNER_TCL_FILE"]="dir::scripts/propagate_clock.tcl"
(R/"config_sta.json").write_text(json.dumps(cfg,indent=2)+"\n")
print("Prepared post-CTS STA with placement-estimated SPEF",spefs[0])
