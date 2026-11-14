from pathlib import Path
from verify_manual_source import verify
import runpy
from librelane.steps import Step
assert verify(Path('/runtime_final/driver51_b.odb'))==0
Step.factory.get('OpenROAD.DetailedRouting').get_script_path=lambda self:'/work/week25_closure/scripts/signal_manual_export.tcl'
runpy.run_module('librelane',run_name='__main__')
