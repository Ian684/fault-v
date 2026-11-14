from pathlib import Path
import json,shutil
r=Path.cwd()
d=Path(r"D:\Codex\WSL\fault-v-asic\design")
cfg=json.loads((r/"config.json").read_text())
assert cfg["CLOCK_PERIOD"]==40 and cfg["SYNTH_STRATEGY"]=="AREA 0"
cfg["SYNTH_ABC_BUFFERING"]=True
(r/"config_buffered.json").write_text(json.dumps(cfg,indent=2),encoding="utf8",newline="\n")
shutil.copy2(r/"config_buffered.json",d/"config_buffered.json")
shutil.copy2(r/"scripts/run_buffered.sh",d/"scripts/run_buffered.sh")
shutil.copy2(r/"config.json",r/"reports/tt_release/input_config.json")
shutil.copy2(r/"source_identity.json",r/"reports/tt_release/source_identity.json")
print("Prepared one-setting buffering experiment; original release inputs retained.")
