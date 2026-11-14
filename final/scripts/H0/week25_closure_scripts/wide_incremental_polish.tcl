source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 4
set_debug_level DRT snapshot 1
detailed_route_debug -snapshot_dir $::env(STEP_DIR)
detailed_route -or_seed 19 -or_k 3 -no_pin_access -single_step_dr -verbose 1 -output_drc $::env(STEP_DIR)/fault_v_asic_top.drc
# The pinned implementation skips DRC/NEARDRC steps with an empty marker table.
# Match FlexDR::main: complete initial routing uses INCR=3, preserving existing copper.
drt::step_dr 7 0 3 16 0 16 0.95 3 1
puts "W25_WIDE_INITIALIZED_DRC [detailed_route_num_drvs]"
foreach {size offset mode cost} {15 -4 2 512 21 -7 2 1024 29 -11 2 2048 15 -6 0 4096} {
    if {[detailed_route_num_drvs] == 0} {break}
    drt::step_dr $size $offset 30 $cost $cost 4096 0.95 $mode 0
    puts "W25_WIDE_STEP size=$size offset=$offset DRC=[detailed_route_num_drvs]"
}
drt::step_end
set count [detailed_route_num_drvs]
write_db $::env(STEP_DIR)/native_final.odb
set antenna [check_antennas -report_file $::env(STEP_DIR)/antenna.rpt]
set digest [lindex [exec sha256sum $::env(STEP_DIR)/native_final.odb] 0]
set f [open $::env(STEP_DIR)/native_pair.json w]
puts $f "{\"native_DRC\":$count,\"antenna_nets\":$antenna,\"odb_sha256\":\"$digest\",\"accepted\":false}"
close $f
puts "W25_WIDE_FINAL DRC=$count antenna=$antenna; independent whole-chip checks required"
write_views
