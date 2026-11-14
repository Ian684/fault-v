source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
source $::env(SCRIPTS_DIR)/openroad/common/resizer.tcl
read_current_odb
set_thread_count 4
set_propagated_clock [all_clocks]
set_dont_touch_objects
set protected [dict create]
foreach name {_30188_ _37463_ _37409_} {
 set inst [$::block findInst $name]
 if {$inst eq "NULL"} {error "Missing protected pin-access cell"}
 dict set protected $name [list [[$inst getMaster] getName] [$inst getLocation] [$inst getOrient] [$inst getPlacementStatus]]
 $inst setPlacementStatus FIRM
}
set inst [$::block findInst _27436_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__a211oi_2"} {error "Unexpected driver _27436_"}
log_cmd replace_cell _27436_ sky130_fd_sc_hd__a211oi_4
set inst [$::block findInst clkbuf_1_1_0_clk]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__clkbuf_8"} {error "Unexpected driver clkbuf_1_1_0_clk"}
set master [[$::block getDataBase] findMaster sky130_fd_sc_hd__clkbuf_16]
if {$master eq "NULL" || ![$inst swapMaster $master]} {error "Clock drive swap failed"}
if {[get_property [get_cells clkbuf_1_1_0_clk] ref_name] ne "sky130_fd_sc_hd__clkbuf_16"} {error "STA did not observe clock swap"}
set inst [$::block findInst _29513_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _29513_"}
log_cmd replace_cell _29513_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _39099_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _39099_"}
log_cmd replace_cell _39099_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _27916_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _27916_"}
log_cmd replace_cell _27916_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _30115_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _30115_"}
log_cmd replace_cell _30115_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _34275_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _34275_"}
log_cmd replace_cell _34275_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _31004_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _31004_"}
log_cmd replace_cell _31004_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _36659_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _36659_"}
log_cmd replace_cell _36659_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _41007_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _41007_"}
log_cmd replace_cell _41007_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _30852_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _30852_"}
log_cmd replace_cell _30852_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _35759_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _35759_"}
log_cmd replace_cell _35759_ sky130_fd_sc_hd__buf_2
set inst [$::block findInst _38114_]
if {$inst eq "NULL" || [[$inst getMaster] getName] ne "sky130_fd_sc_hd__buf_1"} {error "Unexpected driver _38114_"}
log_cmd replace_cell _38114_ sky130_fd_sc_hd__buf_2
set nor [$::block findInst _26002_]
if {[[$nor getMaster] getName] ne "sky130_fd_sc_hd__nor4_4"} {error "Unexpected max-size NOR driver"}
set target [$::block findNet _22463_]
if {$target eq "NULL"} {error "Missing measured high-capacitance net"}
set loads {}
foreach term [$target getITerms] {
 if {[[ $term getMTerm] getIoType] eq "INPUT"} {
  set path "[[$term getInst] getName]/[[$term getMTerm] getName]"
  set loads [concat $loads [get_pins [list $path]]]
 }
}
if {[llength $loads] < 2} {error "NOR branch load selection changed"}
lassign [$nor getLocation] x y
foreach name {eco_desktop_nor_load eco_desktop_hold_a eco_desktop_hold_b eco_desktop_hold_c} {
 if {[$::block findInst $name] ne "NULL" || [$::block findNet "${name}_net"] ne "NULL"} {error "ECO name collision"}
}
log_cmd insert_buffer -load_pins $loads -buffer_cell sky130_fd_sc_hd__buf_4 -location [list [expr {$x/1000.0+10.12}] [expr {$y/1000.0}]] -buffer_name eco_desktop_nor_load -net_name eco_desktop_nor_load_net
set endpoint [$::block findInst _53826_]
if {$endpoint eq "NULL"} {error "Missing measured hold endpoint"}
lassign [$endpoint getLocation] x y
set offset -16.56
foreach name {eco_desktop_hold_a eco_desktop_hold_b eco_desktop_hold_c} {
 log_cmd insert_buffer -load_pins [get_pins _53826_/D] -buffer_cell sky130_fd_sc_hd__buf_1 -location [list [expr {$x/1000.0+$offset}] [expr {$y/1000.0}]] -buffer_name $name -net_name "${name}_net"
 set offset [expr {$offset+5.52}]
}
source $::env(SCRIPTS_DIR)/openroad/common/dpl.tcl
dict for {name old} $protected {
 set inst [$::block findInst $name]
 if {[list [[$inst getMaster] getName] [$inst getLocation] [$inst getOrient]] ne [lrange $old 0 2]} {error "Protected access cell moved"}
 $inst setPlacementStatus [lindex $old 3]
}
unset_dont_touch_objects
log_cmd check_placement -verbose
puts "FAULTV_TARGETED_ELECTRICAL_PROPOSAL 13_resizes_4_buffers"
# Proposal only: clear changed wires, reroute and freshly extract before acceptance.
write_views
