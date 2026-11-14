source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 4
detailed_route -or_seed 7 -no_pin_access -single_step_dr -verbose 1 -output_drc $::env(STEP_DIR)/fault_v_asic_top.drc
# Pinned frBaseTypes.h: DRC=0, ALL=1, NEARDRC=2. Keep complete neighboring routes.
foreach {size offset mode cost} {11 -3 0 512 13 -4 2 1024 15 -2 0 2048} {
    drt::step_dr $size $offset 12 $cost $cost 2048 0.95 $mode 0
    puts "W25_FINISH_STEP size=$size offset=$offset DRC=[detailed_route_num_drvs]"
    if {[detailed_route_num_drvs] == 0} {break}
}
drt::step_end
set count [detailed_route_num_drvs]
write_db $::env(STEP_DIR)/native_final.odb
set antenna [check_antennas -report_file $::env(STEP_DIR)/antenna.rpt]
set digest [lindex [exec sha256sum $::env(STEP_DIR)/native_final.odb] 0]
set f [open $::env(STEP_DIR)/native_pair.json w]
puts $f "{\"native_DRC\":$count,\"antenna_nets\":$antenna,\"odb_sha256\":\"$digest\",\"accepted\":false}"
close $f
puts "W25_FINISH_FINAL DRC=$count antenna=$antenna; independent full DRC required"
write_views
