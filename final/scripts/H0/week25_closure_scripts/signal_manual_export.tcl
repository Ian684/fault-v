source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 2
set count [exec python3 /work/week25_closure/scripts/verify_manual_source.py $::env(CURRENT_ODB)]
if {$count != 0} {error "Independent full/context DRC source is not clean"}
file copy $::env(CURRENT_ODB) $::env(STEP_DIR)/native_final.odb
set digest [lindex [exec sha256sum $::env(STEP_DIR)/native_final.odb] 0]
set antenna [check_antennas -report_file $::env(STEP_DIR)/antenna.rpt]
utl::metric "route__drc_errors" $count
set f [open $::env(STEP_DIR)/native_pair.json w]
puts $f "{\"native_DRC\":$count,\"native_DRC_authority\":\"independent_native_full_context\",\"antenna_nets\":$antenna,\"odb_sha256\":\"$digest\",\"accepted\":false}"
close $f
puts "W25_MANUAL_EXPORT independent_native_DRC=$count antenna=$antenna; exact checked ODB copied, no rerouting"
write_views
