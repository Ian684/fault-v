from pathlib import Path
from verify_manual_source import verify
import json,runpy
from librelane.steps import Step
state=json.loads(Path('/work/week25_closure/antenna_stub_manual_state.json').read_text())
assert verify(Path(state['odb']))==0
Step.factory.get('OpenROAD.DetailedRouting').get_script_path=lambda self:'/work/week25_closure/scripts/signal_manual_export.tcl'
runpy.run_module('librelane',run_name='__main__')
