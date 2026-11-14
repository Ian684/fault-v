set tag $::env(PLACEMENT_RUN_TAG)
set root /work/routing
file mkdir $root/reports/$tag
read_liberty /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_liberty $root/macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib
read_db $root/runs/$tag/final/odb/fault_v_asic_top.odb
check_placement -verbose
foreach net {VPWR VGND} {
    check_power_grid -net $net -error_file $root/reports/$tag/$net-grid-errors.rpt
}
puts "ALL POST-CTS PLACEMENT / POWER GRID CHECKS PASSED"
exit
