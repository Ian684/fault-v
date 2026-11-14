"""Extract an explicitly validated pin-interface view with real LEF port declarations."""
from pathlib import Path
import hashlib,json,runpy,librelane
from librelane.steps import Step
C=Path('/work/week25_closure');source=Path(librelane.__file__).parent/'scripts/magic/extract_spice.tcl';text=source.read_text()
needle='read_pdk_spice\n';assert text.count(needle)==1
annotation='''# Declare the validated 125 SRAM ports on existing pin metal; do not import new macros.
lef read /work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef -annotate
'''
modified=text.replace(needle,needle+annotation)
needle2='cd $extdir\n';assert modified.count(needle2)==1
local='path search [list $extdir]\nputs "FAULTV_CORE_LVS_LOCAL_SEARCH=[path search]"\nflush stdout\n'
modified=modified.replace(needle2,needle2+local)
assert modified.replace(annotation,'').replace(local,'')==text
target=C/'controls/extract_spice_core_lvs.tcl'
if target.exists():assert target.read_text()==modified
else:target.write_text(modified,newline='\n')
receipt=C/'reports/core_lvs_extract_script.json'
record={'pinned_original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'changes':['LEF -annotate declares 125 ports in the already validated physical pin-interface macro.','Search only current native extraction directory for freshly generated ext files.'],'scope':'Core-LVS-only workflow. No manufacturing GDS, technology rules or extraction parameters changed.'}
if receipt.exists():assert json.loads(receipt.read_text())==record
else:receipt.write_text(json.dumps(record,indent=2)+'\n')
Step.factory.get('Magic.SpiceExtraction').get_script_path=lambda self:str(target)
runpy.run_module('librelane',run_name='__main__')
