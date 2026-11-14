set f [open /work/routing/scripts/drt_antenna_focus.tcl]
set text [read $f]
close $f
if {![info complete $text]} {error "Incomplete focus Tcl source"}
if {[llength [info commands drt::step_dr]] != 1 || [llength [info commands drt::step_end]] != 1} {error "Required native step API missing"}
puts "NATIVE FOCUS TCL COMPLETENESS AND STEP API CHECK PASSED"
