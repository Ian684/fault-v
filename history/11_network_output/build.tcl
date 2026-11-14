source create_project.tcl
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis failed"}
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
report_timing_summary -delay_type min_max -report_unconstrained -file logs/timing.rpt
report_drc -file logs/drc.rpt
report_methodology -file logs/methodology.rpt
report_route_status -file logs/route.rpt
foreach type {max min} {
    set paths [get_timing_paths -delay_type $type -max_paths 1]
    if {[llength $paths]==0 || [get_property SLACK $paths]<0} {error "Timing failed: $type"}
}
foreach violation [get_drc_violations -quiet] {
    if {[get_property SEVERITY $violation] in {Error {Critical Warning}}} {error "DRC failed: $violation"}
}
open_bd_design [get_files network.bd]
if {[get_property CONFIG.C_BAUDRATE [get_bd_cells serial_rx]] != 115200 || [get_property CONFIG.C_S_AXI_ACLK_FREQ_HZ [get_bd_cells serial_rx]] != 50000000} {error "UART configuration incorrect"}
file copy -force build/project/fault_v_network.runs/impl_1/network_wrapper.bit fault_v_network.bit
file copy -force build/project/fault_v_network.gen/sources_1/bd/network/hw_handoff/network.hwh fault_v_network.hwh
set uart [get_bd_cells serial_rx]
if {[get_property CONFIG.C_BAUDRATE $uart] != 115200} {error "UART baud rate incorrect"}
puts "NETWORK FPGA BUILD PASSED"

