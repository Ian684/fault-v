# Current design must be routed. Keep all diagnostic severities unchanged.
report_route_status -file logs/route_status.rpt
report_timing_summary -delay_type min_max -report_unconstrained -file logs/route_timing.rpt
report_drc -file logs/drc.rpt
report_methodology -file logs/methodology.rpt
set blackboxes [get_cells -quiet -hier -filter {IS_BLACKBOX == 1}]
set latches [get_cells -quiet -hier -filter {REF_NAME =~ LD*}]
if {[llength $blackboxes] || [llength $latches]} {error "Black box or latch present"}
foreach violation [get_drc_violations -quiet] {
    set severity [get_property SEVERITY $violation]
    if {$severity eq "Error" || $severity eq "Critical Warning"} {error "DRC failed: $violation"}
    # One board/platform warning is retained and described in the report.
    if {$severity eq "Warning" && ![string match "ZPS7-1*" $violation]} {
        error "Unexpected DRC warning: $violation"
    }
}
foreach type {max min} {
    set paths [get_timing_paths -delay_type $type -max_paths 1]
    if {[llength $paths]==0 || [get_property SLACK $paths]<0} {error "Timing failed: $type"}
}
set fh [open logs/route_timing.rpt r];set timing_report [read $fh];close $fh
if {![string match "*All user specified timing constraints are met.*" $timing_report]} {
    error "Timing summary includes violations"
}
foreach label {no_clock unconstrained_internal_endpoints generated_clocks loops latch_loops} {
    if {![regexp "checking $label \\(0\\)" $timing_report]} {error "Unexpected timing check: $label"}
}
puts "FPGA AUDIT PASSED: no latches/black boxes, timing met, only documented ZPS7-1 warning allowed"
