source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 8
set_debug_level DRT snapshot 1
detailed_route_debug -snapshot_dir $::env(STEP_DIR)
detailed_route -or_seed 19 -no_pin_access -droute_end_iter 12 -drc_report_iter_step 1 -verbose 1 -output_drc $::env(STEP_DIR)/fault_v_asic_top.drc
set count [detailed_route_num_drvs]
write_db $::env(STEP_DIR)/native_final.odb
set antenna [check_antennas -report_file $::env(STEP_DIR)/antenna.rpt]
set digest [lindex [exec sha256sum $::env(STEP_DIR)/native_final.odb] 0]
set f [open $::env(STEP_DIR)/native_pair.json w]
puts $f "{\"native_DRC\":$count,\"antenna_nets\":$antenna,\"odb_sha256\":\"$digest\",\"accepted\":false}"
close $f
puts "SHORT_POLISH_FINAL DRC=$count antenna=$antenna; independent gates required"
write_views
