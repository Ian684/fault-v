source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl
read_current_odb
set_thread_count 8
set_propagated_clock [all_clocks]
set_dont_touch_objects
set ap_status [dict create]
foreach name {_30188_ _37463_ _37409_} {
    set inst [$::block findInst $name]
    if {$inst eq "NULL"} {error "Missing pin-access ECO instance"}
    dict set ap_status $name [$inst getPlacementStatus]
    $inst setPlacementStatus FIRM
}

foreach row {
    {_26126_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_26253_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_26294_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_26966_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_27072_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_27779_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_27966_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28272_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28315_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28336_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28342_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28368_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28374_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28407_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28413_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28441_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28648_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_28665_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29271_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29305_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29322_ sky130_fd_sc_hd__nor2_2 sky130_fd_sc_hd__nor2_4}
    {_29402_ sky130_fd_sc_hd__a221oi_2 sky130_fd_sc_hd__a221oi_4}
    {_29492_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29510_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29534_ sky130_fd_sc_hd__nor2_2 sky130_fd_sc_hd__nor2_4}
    {_29608_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29622_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29853_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29914_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29923_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29942_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_29952_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30072_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30073_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30158_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30238_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30239_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30254_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30279_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30280_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30745_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30886_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30890_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30892_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30924_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30926_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_30966_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_31006_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_31270_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_31271_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_32688_ sky130_fd_sc_hd__nor3_2 sky130_fd_sc_hd__nor3_4}
    {_32706_ sky130_fd_sc_hd__nor3_2 sky130_fd_sc_hd__nor3_4}
    {_32729_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_32801_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35123_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35127_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35139_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35534_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35538_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35665_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35667_ sky130_fd_sc_hd__clkbuf_2 sky130_fd_sc_hd__clkbuf_4}
    {_35695_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35704_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35733_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35912_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35920_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_35931_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_37072_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_37160_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_37174_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_37181_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_37422_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_37443_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_37510_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_37867_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_38202_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_38679_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39075_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39158_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39170_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39200_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39217_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39229_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39234_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39263_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39277_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39322_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39338_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39343_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39368_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39436_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_39880_ sky130_fd_sc_hd__nor4b_2 sky130_fd_sc_hd__nor4b_4}
    {_40687_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_40702_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_40904_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_41014_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_41223_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_42638_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_42894_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_42928_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_43164_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_43792_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_44273_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_47284_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_47472_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_48691_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_48695_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_48696_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_48749_ sky130_fd_sc_hd__xnor2_2 sky130_fd_sc_hd__xnor2_4}
    {_48760_ sky130_fd_sc_hd__a21oi_2 sky130_fd_sc_hd__a21oi_4}
    {_49560_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_49974_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_50244_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {_50268_ sky130_fd_sc_hd__buf_1 sky130_fd_sc_hd__buf_4}
    {clkbuf_1_0_0_clk sky130_fd_sc_hd__clkbuf_8 sky130_fd_sc_hd__clkbuf_16}
} {
    lassign $row name old new
    set inst [$::block findInst $name]
    if {$inst eq "NULL" || [[$inst getMaster] getName] ne $old} {error "Unexpected resize source $name"}
    if {[[$::block getDataBase] findMaster $new] eq "NULL"} {error "Missing replacement $new"}
    log_cmd replace_cell $name $new
}

foreach row {
    {0 {_53019_/D} {_53019_} {D} 2}
    {1 {u_soc.u_imem.banks\[6\].u_sram/din0[23]} {u_soc.u_imem.banks\[6\].u_sram} {din0[23]} 1}
    {2 {u_soc.u_imem.banks\[6\].u_sram/din0[20]} {u_soc.u_imem.banks\[6\].u_sram} {din0[20]} 1}
    {3 {u_soc.u_imem.banks\[6\].u_sram/din0[9]} {u_soc.u_imem.banks\[6\].u_sram} {din0[9]} 1}
    {4 {u_soc.u_imem.banks\[6\].u_sram/din0[8]} {u_soc.u_imem.banks\[6\].u_sram} {din0[8]} 1}
    {5 {u_soc.u_imem.banks\[6\].u_sram/din0[15]} {u_soc.u_imem.banks\[6\].u_sram} {din0[15]} 1}
    {6 {u_soc.u_imem.banks\[6\].u_sram/din0[13]} {u_soc.u_imem.banks\[6\].u_sram} {din0[13]} 1}
    {7 {u_soc.u_imem.banks\[6\].u_sram/din0[16]} {u_soc.u_imem.banks\[6\].u_sram} {din0[16]} 1}
    {8 {u_soc.u_imem.banks\[6\].u_sram/din0[14]} {u_soc.u_imem.banks\[6\].u_sram} {din0[14]} 1}
    {9 {u_soc.u_imem.banks\[6\].u_sram/din0[11]} {u_soc.u_imem.banks\[6\].u_sram} {din0[11]} 1}
    {10 {u_soc.u_imem.banks\[6\].u_sram/din0[22]} {u_soc.u_imem.banks\[6\].u_sram} {din0[22]} 1}
    {11 {u_soc.u_imem.banks\[6\].u_sram/din0[7]} {u_soc.u_imem.banks\[6\].u_sram} {din0[7]} 1}
    {12 {u_soc.u_imem.banks\[6\].u_sram/din0[3]} {u_soc.u_imem.banks\[6\].u_sram} {din0[3]} 1}
    {13 {u_soc.u_imem.banks\[6\].u_sram/din0[19]} {u_soc.u_imem.banks\[6\].u_sram} {din0[19]} 1}
    {14 {u_soc.u_imem.banks\[6\].u_sram/din0[18]} {u_soc.u_imem.banks\[6\].u_sram} {din0[18]} 1}
    {15 {u_soc.u_imem.banks\[6\].u_sram/din0[10]} {u_soc.u_imem.banks\[6\].u_sram} {din0[10]} 1}
} {
    lassign $row index pin_name instance_name port_name count
    set load [get_pins $pin_name]
    if {[llength $load] != 1} {error "Missing exact hold pin $index"}
    set dbpin [[$::block findInst $instance_name] findITerm $port_name]
    lassign [$dbpin getAvgXY] ok x y
    if {!$ok} {error "Cannot locate hold sink"}
    set loc [list [expr {$x / double([$::block getDbUnitsPerMicron])}] [expr {$y / double([$::block getDbUnitsPerMicron])}]]
    for {set k 0} {$k < $count} {incr k} {
        log_cmd insert_buffer -buffer_cell sky130_fd_sc_hd__dlygate4sd3_1 -load_pins $load -location $loc -buffer_name [format postrc_hold_%s_%s $index $k] -net_name [format postrc_hold_net_%s_%s $index $k]
    }
}
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl
dict for {name status} $ap_status {
    set inst [$::block findInst $name]
    $inst setPlacementStatus $status
}
unset_dont_touch_objects
write_views
