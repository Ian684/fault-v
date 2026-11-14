# Run with the working directory set to the package root.
set_param general.maxThreads 2
source create_project.tcl
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis did not complete"}
open_run synth_1
report_utilization -hierarchical -file logs/synth_utilization.rpt
write_checkpoint -force build/fault_v_synth.dcp
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation did not complete"}
open_run impl_1
report_utilization -file logs/route_utilization.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file logs/route_timing.rpt
report_clock_utilization -file logs/clock_utilization.rpt
report_clocks -file logs/clocks.rpt
report_drc -file logs/drc.rpt
report_methodology -file logs/methodology.rpt
report_cdc -file logs/cdc.rpt
report_route_status -file logs/route_status.rpt
write_checkpoint -force build/fault_v_routed.dcp
file copy -force build/project/fault_v_z2.runs/impl_1/fault_v_fpga_top.bit build/fault_v_fpga_top.bit
set setup [get_timing_paths -delay_type max -max_paths 1]
set hold [get_timing_paths -delay_type min -max_paths 1]
if {[llength $setup]==0 || [llength $hold]==0} {error "No timed paths"}
if {[get_property SLACK $setup]<0 || [get_property SLACK $hold]<0} {error "Timing failed"}
if {[llength [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]]!=0} {error "Unresolved black boxes"}
source audit_design.tcl
puts "FPGA BUILD PASSED: routed design, nonnegative setup/hold slack, bitstream generated"
