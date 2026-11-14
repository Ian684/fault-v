create_clock -name core_clk -period 40.0 [get_ports clk]
set_clock_uncertainty 0.25 [get_clocks core_clk]
set_clock_transition 0.15 [get_clocks core_clk]
set_input_delay -max 4.0 -clock core_clk [get_ports {uart_rx gpio_in[*]}]
set_input_delay -min 0.5 -clock core_clk [get_ports {uart_rx gpio_in[*]}]
set_input_transition 0.2 [get_ports {uart_rx gpio_in[*]}]
set_output_delay -max 4.0 -clock core_clk [all_outputs]
set_output_delay -min 0.5 -clock core_clk [all_outputs]
set_load 0.03 [all_outputs]
# External reset assertion is asynchronous; release is synchronized internally.
# Exception limited to the three asynchronous reset synchronizer controls.
set reset_targets [get_pins {_54687_/SET_B _54688_/SET_B _54689_/SET_B}]
if {[llength $reset_targets] != 3} {error "Reset endpoint mismatch"}
set_false_path -from [get_ports reset_n] -to $reset_targets
# External asynchronous inputs terminate only at their first sampling FF.
foreach {port pin} {uart_rx _53019_/D {gpio_in[0]} _52931_/D {gpio_in[1]} _52932_/D} {
    set src [get_ports $port]
    set dst [get_pins $pin]
    if {[llength $src] != 1 || [llength $dst] != 1} {error "CDC endpoint mismatch"}
    set_false_path -from $src -to $dst
}
