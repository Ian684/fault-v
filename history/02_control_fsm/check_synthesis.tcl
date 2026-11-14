set root [file dirname [info script]]
read_verilog -sv [list "$root/rtl/fault_v_pkg.sv" "$root/rtl/control_fsm.sv"]
synth_design -top control_fsm -part xc7z020clg400-1 -mode out_of_context
report_utilization -file "$root/logs/control_fsm_utilization.rpt"
set inferred_latches [get_cells -hierarchical -filter {REF_NAME =~ LD*}]
if {[llength $inferred_latches] != 0} { error "Inferred latches: $inferred_latches" }
set flops [get_cells -hierarchical -filter {REF_NAME =~ FD*}]
if {[llength $flops] == 0} { error "No synthesized flip-flops available" }
set blackboxes [get_cells -hierarchical -filter {IS_BLACKBOX == 1}]
if {[llength $blackboxes] != 0} { error "Unresolved black boxes: $blackboxes" }
write_checkpoint -force "$root/sim/control_fsm_synth.dcp"
puts "CONTROL FSM NETLIST STRUCTURE CHECK PASSED; inferred_latches=0; flip_flops=[llength $flops]"
puts "CONTROL FSM SYNTHESIS PASSED; inferred_latches=0"
