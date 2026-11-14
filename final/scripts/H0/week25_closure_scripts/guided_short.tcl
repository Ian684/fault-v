source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 4
detailed_route -or_seed 19 -or_k 3 -no_pin_access -single_step_dr -verbose 1 -output_drc $::env(STEP_DIR)/fault_v_asic_top.drc
drt::step_dr 7 0 3 16 0 16 0.95 3 1
puts "W25_GUIDED_INITIALIZED_DRC [detailed_route_num_drvs]"
foreach cost {32 128 512 2048} {
    if {[detailed_route_num_drvs] == 0} {break}
    drt::step_dr 7 0 16 $cost $cost 1024 0.95 2 0
    puts "W25_GUIDED_REPAIR cost=$cost DRC=[detailed_route_num_drvs]"
}
drt::step_end
set count [detailed_route_num_drvs]
write_db $::env(STEP_DIR)/native_final.odb
set antenna [check_antennas -report_file $::env(STEP_DIR)/antenna.rpt]
set digest [lindex [exec sha256sum $::env(STEP_DIR)/native_final.odb] 0]
set f [open $::env(STEP_DIR)/native_pair.json w]
puts $f "{\"native_DRC\":$count,\"antenna_nets\":$antenna,\"odb_sha256\":\"$digest\",\"accepted\":false}"
close $f
puts "W25_GUIDED_FINAL DRC=$count antenna=$antenna; independent full checks required"
write_views
