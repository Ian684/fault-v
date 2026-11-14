import runpy
from librelane.steps import Step
cls=Step.factory.get("OpenROAD.GlobalRouting")
cls.get_script_path=lambda self:"/work/routing/scripts/grt_partial_rc.tcl"
runpy.run_module("librelane",run_name="__main__")
