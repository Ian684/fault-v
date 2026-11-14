source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl
read_current_odb
set_thread_count 8
set_propagated_clock [all_clocks]
set_dont_touch_objects
set ap_cells [dict create]
foreach name {_30188_ _37463_ _37409_} {
    set inst [$::block findInst $name]
    if {$inst eq "NULL"} {error "Missing protected access cell"}
    dict set ap_cells $name [list [[$inst getMaster] getName] [$inst getLocation] [$inst getOrient] [$inst getPlacementStatus]]
    $inst setPlacementStatus FIRM
}
foreach name {
    _28435_
    _30256_
    _30378_
    _30704_
    _30744_
    _30964_
    _32730_
    _35653_
    _37410_
    _38580_
    _40253_
    _43160_
} {
    set inst [$::block findInst $name]
    if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected data driver source $name"}
    log_cmd replace_cell $name sky130_fd_sc_hd__buf_2
}
source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl
log_cmd read_spef -corner nom_tt_025C_1v80 /work/routing/inputs/rc_followup.nom.spef
est::set_parasitics_src "detailed_routing"
if {[llength [info commands rsz::repair_net_cmd]] != 1} {error "Pinned targeted net repair API unavailable"}
set net [sta::get_net_arg "clock branch repair" clknet_1_0_0_clk]
puts "FAULTV_TARGETED_CLOCK_BRANCH_BEFORE [llength [$::block getInsts]]"
# Only this measured branch is repaired; the API takes distance in STA meters.
log_cmd rsz::repair_net_cmd $net [sta::distance_ui_sta 400] 15.0 15.0
puts "FAULTV_TARGETED_CLOCK_BRANCH_AFTER [llength [$::block getInsts]]"
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl
dict for {name old} $ap_cells {
    set inst [$::block findInst $name]
    if {[list [[$inst getMaster] getName] [$inst getLocation] [$inst getOrient]] ne [lrange $old 0 2]} {error "Protected pin-access cell moved"}
    $inst setPlacementStatus [lindex $old 3]
}
unset_dont_touch_objects
log_cmd check_placement -verbose
# Proposal only: affected routes must be rebuilt and newly extracted before acceptance.
write_views
