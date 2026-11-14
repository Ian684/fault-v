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
foreach name {eco_clock_remote_a eco_clock_remote_b} {
    if {[$::block findInst $name] ne "NULL" || [$::block findNet [format "%s_net" $name]] ne "NULL"} {error "Clock ECO name collision"}
}
set loads [get_pins {clkbuf_leaf_8_clk/A clkbuf_leaf_9_clk/A}]
if {[llength $loads] != 2} {error "Clock branch sink selection changed"}
# Legal seed corridors between SRAM rows; detailed placement snaps to actual sites.
log_cmd insert_buffer -load_pins $loads -buffer_cell sky130_fd_sc_hd__clkbuf_16 -location {850 1110} -buffer_name eco_clock_remote_a -net_name eco_clock_remote_a_net
log_cmd insert_buffer -load_pins $loads -buffer_cell sky130_fd_sc_hd__clkbuf_16 -location {485 610} -buffer_name eco_clock_remote_b -net_name eco_clock_remote_b_net
foreach name {eco_clock_remote_a_net eco_clock_remote_b_net} {
    set net [$::block findNet $name]
    if {$net eq "NULL"} {error "Missing inserted clock branch"}
    $net setSigType CLOCK
}
puts "FAULTV_INSERTED_CLOCK_BRANCH_BUFFERS 2"
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
