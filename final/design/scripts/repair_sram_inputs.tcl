set eco_dir /work/design/eco
file mkdir $eco_dir
proc eco_dump {path} {
 set f [open $path w]
 foreach cell [get_cells -hierarchical *] {
  set inst [get_full_name $cell]
  set ref [get_property $cell ref_name]
  foreach pin [get_pins -of_objects $cell] {
   set nets [get_nets -of_objects $pin]
   if {[llength $nets] == 1 && [lindex $nets 0] != "NULL"} {
    puts $f "$inst\t$ref\t[get_full_name $pin]\t[get_full_name [lindex $nets 0]]"
   }
  }
 }
 set ports 0
 foreach net [get_nets *] {
  foreach port [get_ports -of_objects $net] {
   incr ports
   puts $f "TOP\tPORT\t[get_full_name $port]\t[get_full_name $net]"
  }
 }
 close $f
 if {$ports != 108} {error "Expected 108 top port bits, got $ports"}
}
eco_dump $eco_dir/before.tsv
set cap_cell [get_cells _29323_]
if {[llength $cap_cell] != 1} {error "Expected one overloaded buffer"}
set old_ref [get_property $cap_cell ref_name]
if {![regexp {sky130_fd_sc_hd__buf_[0-9]+$} $old_ref]} {error "Unexpected overloaded cell $old_ref"}
replace_cell $cap_cell sky130_fd_sc_hd__buf_16
set targets [concat [get_pins */addr0*] [get_pins */wmask0*]]
set selected {}
foreach pin $targets {
 if {[regexp {/(addr0|wmask0)\[[0-9]+\]$} [get_full_name $pin]]} {lappend selected $pin}
}
if {[llength $selected] != 234} {error "Expected 234 SRAM inputs, got [llength $selected]"}
set index 0
foreach pin $selected {
 set source [lindex [get_nets -of_objects $pin] 0]
 set b1 eco_sram_b${index}_first
 set b2 eco_sram_b${index}_last
 set n1 eco_sram_n${index}_first
 set n2 eco_sram_n${index}_last
 make_instance $b1 sky130_fd_sc_hd__buf_4
 make_instance $b2 sky130_fd_sc_hd__buf_16
 make_net $n1
 make_net $n2
 disconnect_pin $source $pin
 connect_pin $source $b1/A
 connect_pin $n1 $b1/X
 connect_pin $n1 $b2/A
 connect_pin $n2 $b2/X
 connect_pin $n2 $pin
 incr index
}
eco_dump $eco_dir/after.tsv
write_verilog $eco_dir/fault_v_asic_top.nl.v
set area 0.0
set flops 0
set macros 0
foreach cell [get_cells -hierarchical *] {
 set ref [get_property $cell ref_name]
 if {[string match *sky130_sram* $ref]} {incr macros} else {
  set area [expr {$area + [get_property [get_lib_cells $ref] area]}]
 }
 if {[regexp {sky130_fd_sc_hd__df} $ref]} {incr flops}
}
if {$flops != 2925 || $macros != 18} {error "Unexpected state/macro counts: $flops/$macros"}
write_metric_num design__instance__area $area
write_metric_int design__instance__count [llength [get_cells -hierarchical *]]
puts "ECO: isolated $index SRAM inputs; upsized $old_ref; flops=$flops macros=$macros area=$area"
