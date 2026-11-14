source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 8
set_propagated_clock [all_clocks]
foreach name {
    _26126_
    _26253_
    _26294_
    _26966_
    _27072_
    _27779_
    _27966_
    _28272_
    _28315_
    _28336_
    _28342_
    _28368_
    _28374_
    _28407_
    _28413_
    _28441_
    _28648_
    _28665_
    _29271_
    _29305_
    _29492_
    _29510_
    _29608_
    _29622_
    _29853_
    _29914_
    _29923_
    _29942_
    _29952_
    _30072_
    _30073_
    _30158_
    _30238_
    _30239_
    _30254_
    _30279_
    _30280_
    _30745_
    _30886_
    _30890_
    _30892_
    _30924_
    _30926_
    _30966_
    _31006_
    _31270_
    _31271_
    _32729_
    _32801_
    _35123_
    _35127_
    _35139_
    _35534_
    _35538_
    _35665_
    _35695_
    _35704_
    _35733_
    _35912_
    _35920_
    _35931_
    _37072_
    _37160_
    _37174_
    _37181_
    _37422_
    _37443_
    _37510_
    _37867_
    _38202_
    _38679_
    _39075_
    _39158_
    _39170_
    _39200_
    _39217_
    _39229_
    _39234_
    _39263_
    _39277_
    _39322_
    _39338_
    _39343_
    _39368_
    _39436_
    _40687_
    _40702_
    _40904_
    _41014_
    _41223_
    _42638_
    _42894_
    _42928_
    _43164_
    _43792_
    _44273_
    _47284_
    _47472_
    _48691_
    _48695_
    _48696_
    _49560_
    _49974_
    _50244_
    _50268_
} {
    set inst [$::block findInst $name]
    if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_4"} {error "Unexpected shrink source $name"}
    set box [$inst getBBox]
    set before [list [$box xMin] [$box yMin] [$box xMax] [$box yMax]]
    set orient [$inst getOrient]
    log_cmd replace_cell $name sky130_fd_sc_hd__buf_2
    set box [$inst getBBox]
    if {[$box xMin] < [lindex $before 0] || [$box yMin] < [lindex $before 1] || [$box xMax] > [lindex $before 2] || [$box yMax] > [lindex $before 3] || [$inst getOrient] ne $orient} {
        error "Replacement footprint grew or orientation changed: $name"
    }
}
log_cmd check_placement -verbose
write_views
