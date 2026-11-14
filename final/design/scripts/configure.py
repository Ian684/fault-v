from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
cfg=json.loads((R/'config_electrical.json').read_text(encoding='utf8'))
cfg['STA_EXTRA_CORNER_TCL_FILE']='dir::scripts/repair_sram_inputs.tcl'
(R/'config.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf8',newline='\n')
files=[p.removeprefix('dir::') for p in cfg['VERILOG_FILES']]
files+=['constraints.sdc','config.json','scripts/repair_sram_inputs.tcl','scripts/sta310_cli.py']
m=next(iter(cfg['MACROS']))
files+=['macros/vendor/'+m+'_TT_1p8V_25C.lib','macros/vendor/'+m+'.lef','macros/vendor/'+m+'.gds']
hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in files}
(R/'source_identity.json').write_text(json.dumps(hashes,indent=2)+'\n',encoding='utf8')
print('Configured buffered synthesis and bounded SRAM-input ECO; hashed',len(hashes),'inputs.')
