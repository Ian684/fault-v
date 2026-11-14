set_propagated_clock [all_clocks]
foreach clock [all_clocks] {
    if {![get_property $clock is_propagated]} {error "Clock is not propagated"}
}
puts "FAULTV_PROPAGATED_CLOCKS_VERIFIED"
# Populate timing before reading pin properties.
report_checks -path_delay max -group_path_count 1
set selected {}
foreach pin [concat [get_pins */addr0*] [get_pins */wmask0*]] {
    if {[regexp {/(addr0|wmask0)\[[0-9]+\]$} [get_full_name $pin]]} {
        lappend selected $pin
    }
}
if {[llength $selected] != 234} {error "Expected 234 SRAM constrained inputs"}
set worst 0.0
set worst_pin {}
foreach pin $selected {
    set value [get_property $pin slew_max]
    if {$value > $worst} {set worst $value;set worst_pin [get_full_name $pin]}
}
puts "FAULTV_MAX_MACRO_INPUT_SLEW_NS $worst PIN $worst_pin"
