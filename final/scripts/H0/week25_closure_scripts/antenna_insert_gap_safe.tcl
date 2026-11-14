source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 4
set diode_cell [lindex [split $::env(DIODE_CELL) /] 0]
set before [check_antennas -report_file $::env(STEP_DIR)/baseline_antenna.rpt]
puts "W25_ANTENNA_BEFORE $before"
set block [ord::get_db_block]
# Pinned inserter skips existing names only at construction, then increments blindly.
set tap_name TAP_TAPCELL_ROW_0_8384
set tap [$block findInst $tap_name]
if {$tap == "NULL" || [$block findInst ANTENNA_7502] != "NULL"} {error "Name-gap workaround precondition failed"}
if {![$tap rename ANTENNA_7502]} {error "Temporary tap alias failed"}
if {$before > 0} {
    repair_antennas $diode_cell -ratio_margin 0 -diode_only
    global_connect
}
if {![$tap rename $tap_name]} {error "Tap name restoration failed"}
if {[$block findInst ANTENNA_7502] != "NULL" || [$block findInst $tap_name] != $tap} {error "Temporary alias survived"}
check_placement -verbose
write_db $::env(STEP_DIR)/inserted.odb
set digest [lindex [exec sha256sum $::env(STEP_DIR)/inserted.odb] 0]
set f [open $::env(STEP_DIR)/insertion.json w]
puts $f "{\"accepted\":false,\"baseline_antenna_nets\":$before,\"output_sha256\":\"$digest\",\"temporary_tap_alias_restored\":true}"
close $f
write_views
