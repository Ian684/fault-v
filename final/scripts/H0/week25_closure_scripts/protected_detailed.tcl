source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 4
set_debug_level DRT snapshot 1
detailed_route_debug -snapshot_dir $::env(STEP_DIR)
pin_access
write_db $::env(STEP_DIR)/native_pin_access.odb
detailed_route -no_pin_access -droute_end_iter 64 -drc_report_iter_step 1 -verbose 1 -output_drc $::env(STEP_DIR)/fault_v_asic_top.drc
set count [detailed_route_num_drvs]
write_db $::env(STEP_DIR)/protected_final.odb
puts "PROTECTED_ROUTING_COUNT $count; normalization and independent DRC still required"
write_views
