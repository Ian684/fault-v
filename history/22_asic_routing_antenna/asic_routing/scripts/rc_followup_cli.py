import runpy
from librelane.steps import Step
cls=Step.factory.get("OpenROAD.RepairDesignPostGRT")
assert cls.get_script_path.__name__=="get_script_path"
cls.get_script_path=lambda self:"/work/routing/scripts/repair_rc_followup.tcl"
runpy.run_module("librelane",run_name="__main__")
