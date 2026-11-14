"""Use the verified STA binary while retaining LibreLane's exact analysis script."""
import runpy
from librelane.steps import Step
cls=Step.factory.get("OpenROAD.STAPrePNR")
original=cls.get_command
def fixed_sta_command(self):
 command=original(self)
 assert command[0]=="sta"
 command[0]="/work/routing/sta_tool/sta"
 return command
cls.get_command=fixed_sta_command
runpy.run_module("librelane",run_name="__main__")
