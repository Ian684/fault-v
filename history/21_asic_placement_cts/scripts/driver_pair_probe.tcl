read_liberty /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_liberty /work/placement_cts/macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib
read_verilog /work/placement_cts/verify/driver_pair_probe.v
link_design driver_pair_probe
create_clock -period 40 [get_ports clk]
set_input_delay 0 -clock clk [get_ports a]
set_input_transition 0.2 [get_ports a]
set_load -wire_load 0.007 [get_nets m0]
set_load -wire_load 0.007 [get_nets m1]
set_load -wire_load 0.007 [get_nets m2]
set_load -wire_load 0.007 [get_nets m3]
set_load -wire_load 0.007 [get_nets m4]
set_load -wire_load 0.007 [get_nets m5]
set_load -wire_load 0.007 [get_nets m6]
set_load -wire_load 0.007 [get_nets m7]
report_checks -from [get_ports a] -group_count 20 -digits 9
puts "PAIR first=buf_4 last=buf_16 rise=[get_property [get_pins {s0/wmask0[0]}] slew_max_rise] fall=[get_property [get_pins {s0/wmask0[0]}] slew_max_fall]"
puts "PAIR first=buf_8 last=buf_16 rise=[get_property [get_pins {s1/wmask0[0]}] slew_max_rise] fall=[get_property [get_pins {s1/wmask0[0]}] slew_max_fall]"
puts "PAIR first=buf_16 last=buf_16 rise=[get_property [get_pins {s2/wmask0[0]}] slew_max_rise] fall=[get_property [get_pins {s2/wmask0[0]}] slew_max_fall]"
puts "PAIR first=clkbuf_8 last=clkbuf_16 rise=[get_property [get_pins {s3/wmask0[0]}] slew_max_rise] fall=[get_property [get_pins {s3/wmask0[0]}] slew_max_fall]"
puts "PAIR first=inv_4 last=inv_16 rise=[get_property [get_pins {s4/wmask0[0]}] slew_max_rise] fall=[get_property [get_pins {s4/wmask0[0]}] slew_max_fall]"
puts "PAIR first=inv_8 last=inv_16 rise=[get_property [get_pins {s5/wmask0[0]}] slew_max_rise] fall=[get_property [get_pins {s5/wmask0[0]}] slew_max_fall]"
puts "PAIR first=inv_16 last=inv_16 rise=[get_property [get_pins {s6/wmask0[0]}] slew_max_rise] fall=[get_property [get_pins {s6/wmask0[0]}] slew_max_fall]"
puts "PAIR first=inv_4 last=inv_12 rise=[get_property [get_pins {s7/wmask0[0]}] slew_max_rise] fall=[get_property [get_pins {s7/wmask0[0]}] slew_max_fall]"
exit
