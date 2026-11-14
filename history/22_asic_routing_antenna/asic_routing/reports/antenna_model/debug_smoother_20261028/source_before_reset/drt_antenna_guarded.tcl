source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count $::env(DRT_THREADS)
set_debug_level DRT snapshot 1
if {[check_antennas] != 0} {error "Guarded input must have zero antenna violations"}
set best 110
set stalls 0
set phase 0
set violations -1
# Each stage commits native routes before measuring antenna on that same database.
# No ALL rip-up, temporary FIXED flags, extra diodes or physical-rule changes.
foreach {size offset maze cost mode} {13 0 4 32 2 19 -1 6 64 2 13 -2 6 128 0 19 0 8 256 0} {
    incr phase
    set directory $::env(STEP_DIR)/guarded_$phase
    file mkdir $directory
    detailed_route_debug -snapshot_dir $directory
    set started [clock seconds]
    detailed_route -no_pin_access -single_step_dr -droute_end_iter $::env(DRT_OPT_ITERS) -drc_report_iter_step 1 -verbose 1 -output_drc $directory/$::env(DESIGN_NAME).drc
    drt::step_dr 9 0 3 8 0 8 0.95 3 1
    drt::step_dr 9 -1 3 8 0 8 0.95 3 1
    puts "ANTENNA_GUARDED_BASELINE phase=$phase DRC=[detailed_route_num_drvs]"
    if {[detailed_route_num_drvs] != 0} {
        drt::step_dr $size $offset $maze $cost $cost 128 0.95 $mode 0
    }
    # step_end writes the internal native router geometry back to OpenDB.
    drt::step_end
    set violations [detailed_route_num_drvs]
    set odb_file guarded_stage_${phase}.odb
    set odb_path $::env(STEP_DIR)/$odb_file
    write_db $odb_path
    set remaining [check_antennas]
    set digest [lindex [exec sha256sum $odb_path] 0]
    if {![regexp {^[0-9a-f]{64}$} $digest]} {error "Invalid checkpoint hash"}
    set elapsed [expr {[clock seconds]-$started}]
    set proof $::env(STEP_DIR)/guarded_stage_${phase}.json
    set f [open ${proof}.tmp w]
    puts $f "{\"stage\":$phase,\"odb_file\":\"$odb_file\",\"odb_sha256\":\"$digest\",\"native_DRC\":$violations,\"antenna_nets\":$remaining,\"elapsed_seconds\":$elapsed,\"accepted\":false}"
    close $f
    file rename ${proof}.tmp $proof
    puts "ANTENNA_GUARDED_PAIR stage=$phase DRC=$violations antenna=$remaining elapsed_seconds=$elapsed"
    if {$remaining != 0} {error "Guarded stage reintroduced $remaining antenna nets; checkpoint retained"}
    if {$violations == 0} {break}
    if {$violations < $best} {set best $violations;set stalls 0} else {incr stalls}
    if {$stalls >= 2} {error "Two stages without a new zero-antenna DRC best; checkpoints retained"}
}
if {$violations != 0} {error "Guarded routing incomplete: $violations DRC; checkpoints retained"}
puts "ANTENNA_CLOSURE_NATIVE_ZERO"
write_views
