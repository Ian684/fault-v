"""Keep the reviewed IR load/feeds, additionally export the exact native PG circuit."""
from pathlib import Path
import runpy
from librelane.steps import Step
C=Path('/work/week25_closure')
original=Path('/work/week25_signoff/scripts/ir_review.tcl').read_text()
line='    analyze_power_grid -net $net -vsrc $vsrc -voltage_file $::env(STEP_DIR)/net-$net.csv -enable_em -em_outfile $::env(STEP_DIR)/em-$net.csv -error_file $::env(STEP_DIR)/analysis-$net.rpt'
assert original.count(line)==1
updated=original.replace(line,line+'\n    write_pg_spice -net $net -vsrc $vsrc $::env(STEP_DIR)/network-$net.spice')
target=C/'controls/pg_ir_with_network.tcl'
if target.exists():assert target.read_text()==updated
else:target.write_text(updated)
Step.factory.get('OpenROAD.IRDropReport').get_script_path=lambda self:str(target)
runpy.run_module('librelane',run_name='__main__')
