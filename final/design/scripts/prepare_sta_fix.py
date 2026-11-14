from pathlib import Path
import json,shutil
r=Path.cwd();d=Path(r"D:\Codex\WSL\fault-v-asic\design")
for n in ["install_sta_dependencies.sh","build_sta_fixed.sh"]:
 shutil.copy2(r/"scripts"/n,d/"scripts"/n)
cfg=json.loads((r/"config_buffered.json").read_text())
cfg.update(MAX_TRANSITION_CONSTRAINT=0.03,SYNTH_DIRECT_WIRE_BUFFERING=False)
(r/"config_slew.json").write_text(json.dumps(cfg,indent=2),encoding="utf8",newline="\n")
shutil.copy2(r/"config_slew.json",d/"config_slew.json")
s=(r/"scripts/run_buffered.sh").read_text().replace("tt_buffered","tt_slew").replace("config_buffered.json","config_slew.json")
(r/"scripts/run_slew.sh").write_text(s,encoding="utf8",newline="\n")
shutil.copy2(r/"scripts/run_slew.sh",d/"scripts/run_slew.sh")
