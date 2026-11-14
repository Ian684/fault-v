import runpy
from librelane.steps import Step
Step.factory.get('OpenROAD.IRDropReport').get_script_path=lambda self:'/work/ppa/h1/cand_gap90x95/closure_c/controls/h1_ir_native.tcl'
runpy.run_module('librelane',run_name='__main__')
