"""Use freshly generated local extraction files after loading the complete GDS."""
from pathlib import Path
import hashlib,json,runpy,librelane
from librelane.steps import Step
C=Path('/work/week25_closure')
source=Path(librelane.__file__).parent/'scripts/magic/extract_spice.tcl'
text=source.read_text();needle='cd $extdir\n'
assert text.count(needle)==1
addition='''# All cells and port orders have already been loaded from the full GDS/PDK SPICE.
# Avoid millions of failed .ext lookups in unrelated PDK libraries over 9P.
path search [list $extdir]
puts "FAULTV_NATIVE_EXT_SEARCH=[path search] LOADED_CELLS=[llength [cellname list allcells]]"
flush stdout
'''
modified=text.replace(needle,needle+addition)
assert modified.replace(addition,'')==text
target=C/'controls/extract_spice_native_search.tcl'
if target.exists():assert target.read_text()==modified
else:target.write_text(modified,newline='\n')
(C/'reports/native_magic_search_source.json').write_text(json.dumps({'pinned_original_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'only_change':'Set extraction search path to native STEP_DIR/extraction after full GDS loading, PDK port-order annotation and explicit SRAM abstraction. Extraction settings, geometry, models and rules are unchanged. All outputs freshly generated; no old external .ext reused.'},indent=2)+'\n')
Step.factory.get('Magic.SpiceExtraction').get_script_path=lambda self:str(target)
runpy.run_module('librelane',run_name='__main__')
