source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 4
set diode_cell [lindex [split $::env(DIODE_CELL) /] 0]
set before [check_antennas -report_file $::env(STEP_DIR)/baseline_antenna.rpt]
puts "W25_ANTENNA_BEFORE $before"
if {$before > 0} {
    repair_antennas $diode_cell -ratio_margin 0 -diode_only
    global_connect
}
check_placement -verbose
write_db $::env(STEP_DIR)/inserted.odb
set digest [lindex [exec sha256sum $::env(STEP_DIR)/inserted.odb] 0]
set f [open $::env(STEP_DIR)/insertion.json w]
puts $f "{\"accepted\":false,\"baseline_antenna_nets\":$before,\"output_sha256\":\"$digest\"}"
close $f
write_views
