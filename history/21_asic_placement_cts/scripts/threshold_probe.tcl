read_liberty /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_liberty /work/placement_cts/macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib
read_verilog /work/placement_cts/verify/threshold_probe.v
link_design threshold_probe
create_clock -period 40 [get_ports clk]
set_clock_transition 0.15 [get_clocks clk]
set_input_delay 0 -clock clk [get_ports a]
set_input_transition 0.2 [get_ports a]
report_check_types -max_slew -violators -digits 9
report_checks -from [get_ports a] -to [get_pins sram*/wmask0*] -group_count 32 -fields {slew cap fanout} -digits 9
exit
