"""Analyze the actual final netlist using global-route RC or extracted routed RC."""
from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
tag,scope=sys.argv[1:3]
assert tag.replace("_","").isalnum() and scope in ["global","routed"]
run=R/"runs"/tag
if scope=="global":
    spefs=list(run.glob("*-openroad-stamidpnr/estimated_global.spef"))
else:
    spefs=[p for p in (run/"final/spef").rglob("*.spef") if "nom" in p.name and "min" not in p.name and "max" not in p.name]
assert len(spefs)==1 and spefs[0].stat().st_size>100000,spefs
nl=list((run/"final/nl").glob("*.v"));assert len(nl)==1
state={"nl":"/work/routing/"+nl[0].relative_to(R).as_posix(),"spef":{"nom_tt_025C_1v80":"/work/routing/"+spefs[0].relative_to(R).as_posix()},"metrics":{}}
(R/f"sta_state_{tag}.json").write_text(json.dumps(state,indent=2)+"\n")
physical=json.loads((R/"config_global.json").read_text())
keys=["DESIGN_NAME","PDK","STD_CELL_LIBRARY","CLOCK_PORT","CLOCK_PERIOD","DEFAULT_CORNER","STA_CORNERS","PNR_SDC_FILE","SIGNOFF_SDC_FILE","MACROS"]
cfg={k:physical[k] for k in keys}
cfg["meta"]={"version":2,"flow":["OpenROAD.STAPrePNR"]}
cfg["STA_EXTRA_CORNER_TCL_FILE"]="dir::scripts/propagate_clock.tcl"
(R/"config_sta.json").write_text(json.dumps(cfg,indent=2)+"\n")
(R/"reports"/f"{tag}_sta_source.json").write_text(json.dumps({"scope":scope,"spef":str(spefs[0].relative_to(R)),"source_netlist":str(nl[0].relative_to(R))},indent=2)+"\n")
print("Prepared corrected STA:",scope,spefs[0])
