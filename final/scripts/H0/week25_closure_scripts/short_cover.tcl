source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 4
detailed_route -or_seed 7 -no_pin_access -droute_end_iter 16 -drc_report_iter_step 1 -verbose 1 -output_drc $::env(STEP_DIR)/fault_v_asic_top.drc
set count [detailed_route_num_drvs]
write_db $::env(STEP_DIR)/native_final.odb
set antenna [check_antennas -report_file $::env(STEP_DIR)/antenna.rpt]
set digest [lindex [exec sha256sum $::env(STEP_DIR)/native_final.odb] 0]
set f [open $::env(STEP_DIR)/native_pair.json w]
puts $f "{\"native_DRC\":$count,\"antenna_nets\":$antenna,\"odb_sha256\":\"$digest\",\"accepted\":false}"
close $f
puts "SHORT_COVER_FINAL DRC=$count antenna=$antenna; independent DRC required"
write_views
