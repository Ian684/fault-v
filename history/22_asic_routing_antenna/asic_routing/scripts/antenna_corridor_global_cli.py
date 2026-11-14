import runpy
from librelane.steps import Step
cls=Step.factory.get('OpenROAD.GlobalRouting')
assert cls.get_script_path.__name__=='get_script_path'
cls.get_script_path=lambda self:'/work/routing/scripts/grt_antenna_corridor.tcl'
runpy.run_module('librelane',run_name='__main__')
