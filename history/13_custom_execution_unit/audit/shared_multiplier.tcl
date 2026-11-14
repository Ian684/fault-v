set_param general.maxThreads 2
read_verilog -sv rtl/fault_v_pkg.sv
read_verilog -sv rtl/custom_exec.sv
synth_design -top custom_exec -part xc7z020clg400-1
report_utilization -hierarchical -file logs/candidate_utilization.rpt
set dsps [get_cells -hierarchical -filter {REF_NAME == DSP48E1}]
puts "CANDIDATE DSP COUNT: [llength $dsps]"
if {[llength $dsps] != 1} {error "Multiplier sharing not preserved"}
puts "SHARED MULTIPLIER AUDIT PASSED"
