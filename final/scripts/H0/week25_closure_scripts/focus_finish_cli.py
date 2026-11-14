import runpy
from librelane.steps import Step
Step.factory.get('OpenROAD.DetailedRouting').get_script_path=lambda self:'/work/week25_closure/scripts/focus_finish.tcl'
runpy.run_module('librelane',run_name='__main__')
