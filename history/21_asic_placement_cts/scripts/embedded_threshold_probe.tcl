puts "STA_VERSION_CMDS [info commands sta::*version*]"
foreach c [info commands sta::*version*] {if {![catch {$c} v]} {puts "$c = $v"}}
read_lef /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_lef /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_ef_sc_hd.lef
read_lef /work/placement_cts/macros/sky130_sram_2kbyte_1rw1r_32x512_8.lef
source /work/placement_cts/scripts/threshold_probe.tcl
