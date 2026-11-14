"""LibreLane with Magic.SpiceExtraction using H0's validated core-LVS extraction script (read-only).

Same derivation as week25_closure/scripts/core_lvs_cli.py: the pinned extract_spice.tcl plus the SRAM LEF
-annotate line and a local extraction search path. This copy only checks that the frozen W25 script equals
that derivation and uses it; it writes nothing under week25_closure.
"""
from pathlib import Path
import runpy, librelane
from librelane.steps import Step

source = Path(librelane.__file__).parent / 'scripts/magic/extract_spice.tcl'
text = source.read_text()
needle = 'read_pdk_spice\n'
assert text.count(needle) == 1
annotation = '''# Declare the validated 125 SRAM ports on existing pin metal; do not import new macros.
lef read /work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef -annotate
'''
modified = text.replace(needle, needle + annotation)
needle2 = 'cd $extdir\n'
assert modified.count(needle2) == 1
local = 'path search [list $extdir]\nputs "FAULTV_CORE_LVS_LOCAL_SEARCH=[path search]"\nflush stdout\n'
modified = modified.replace(needle2, needle2 + local)
target = Path('/work/week25_closure/controls/extract_spice_core_lvs.tcl')
assert target.read_text() == modified
Step.factory.get('Magic.SpiceExtraction').get_script_path = lambda self: str(target)
runpy.run_module('librelane', run_name='__main__')
