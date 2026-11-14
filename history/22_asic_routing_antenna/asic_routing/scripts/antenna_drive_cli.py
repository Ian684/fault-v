import runpy
from librelane.steps import Step
cls=Step.factory.get('OpenROAD.DetailedRouting')
assert cls.get_script_path.__name__=='get_script_path'
cls.get_script_path=lambda self:'/work/routing/scripts/drt_antenna_drive.tcl'
runpy.run_module('librelane',run_name='__main__')
