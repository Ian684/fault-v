source /work/week25_closure/runs/probe_rc_a/1-openroad-fillinsertion/_env.tcl
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
set ::env(CURRENT_ODB) /work/week25_closure/runs/probe_rc_a/1-openroad-fillinsertion/fault_v_asic_top.odb
read_current_odb
write_verilog -remove_cells {sky130_fd_sc_hd__fill_1 sky130_fd_sc_hd__fill_2 sky130_fd_sc_hd__fill_4 sky130_fd_sc_hd__fill_8 sky130_fd_sc_hd__tapvpwrvgnd_1} /work/week25_closure/inputs/probe_current.nl.v
write_verilog -include_pwr_gnd /work/week25_closure/inputs/probe_current.pnl.v
puts "FAULTV_ACTUAL_RESIZED_NETLIST_EXPORTED"
exit 0
