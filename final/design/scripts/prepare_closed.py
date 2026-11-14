from pathlib import Path
import json
r=Path(__file__).resolve().parents[1]
config=json.loads((r/'config_electrical.json').read_text())
config['STA_EXTRA_CORNER_TCL_FILE']='dir::scripts/repair_sram_inputs.tcl'
(r/'config_closed.json').write_text(json.dumps(config,indent=2)+'\n')
script=(r/'scripts/run_sta310.sh').read_text().replace('tt_sta310','tt_closed').replace('config_electrical.json','config_closed.json')
(r/'scripts/run_closed.sh').write_text(script)
