import runpy
from librelane.steps import Step
Step.factory.get('OpenROAD.IRDropReport').get_script_path=lambda self:'/work/week25_closure/controls/pg_ir_native.tcl'
runpy.run_module('librelane',run_name='__main__')
