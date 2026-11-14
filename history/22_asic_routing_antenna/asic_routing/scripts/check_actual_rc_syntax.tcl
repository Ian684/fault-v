set f [open "/work/routing/scripts/repair_actual_rc.tcl" r]
set code [read $f]
close $f
if {![info complete $code]} {error "Incomplete actual-RC repair Tcl"}
puts "FAULTV_ACTUAL_RC_TCL_COMPLETE"
exit 0
