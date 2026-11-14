read_db /work/routing/runs/routed_antenna_20261026_190111/1-openroad-detailedrouting/antenna_inserted_1.odb
check_placement -verbose
foreach net {VPWR VGND} {
    check_power_grid -net $net -error_file /work/routing/reports/antenna_model/first_insertion_${net}_errors.rpt
}
puts "FIRST_INSERTION_PLACEMENT_AND_POWER_CONNECTED"
exit
