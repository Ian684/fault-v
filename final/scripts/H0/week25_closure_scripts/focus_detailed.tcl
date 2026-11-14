source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 4
set_debug_level DRT snapshot 1
detailed_route_debug -snapshot_dir $::env(STEP_DIR)
detailed_route -no_pin_access -single_step_dr -droute_end_iter 64 -drc_report_iter_step 1 -verbose 1 -output_drc $::env(STEP_DIR)/fault_v_asic_top.drc
drt::step_dr 7 0 8 16 16 128 0.95 1 0
puts "W25_FOCUS_START_DRC [detailed_route_num_drvs]"
foreach {size offset mode cost} {7 -1 2 32 9 -2 2 64 11 0 2 128 9 -1 0 256 11 -2 0 512 13 0 0 1024} {
    if {[detailed_route_num_drvs] == 0} {break}
    drt::step_dr $size $offset 8 $cost $cost 1024 0.95 $mode 0
    puts "W25_FOCUS_STEP size=$size offset=$offset DRC=[detailed_route_num_drvs]"
}
drt::step_end
write_db $::env(STEP_DIR)/focus_final.odb
puts "W25_FOCUS_FINAL_DRC [detailed_route_num_drvs]; normalization required"
write_views
