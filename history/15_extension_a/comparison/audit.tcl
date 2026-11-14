set_param general.maxThreads 1
foreach item {{shared custom_exec_shared 1} {parallel custom_exec_parallel 4}} {
 lassign $item name top expected
 create_project -in_memory -part xc7z020clg400-1
 read_verilog -sv rtl/fault_v_pkg.sv
 read_verilog -sv comparison/${name}_unit.sv
 synth_design -top $top -part xc7z020clg400-1
 report_utilization -file logs/${name}_unit_utilization.rpt
 set count [llength [get_cells -hierarchical -filter {REF_NAME == DSP48E1}]]
 if {$count != $expected} {error "Unexpected multiplier count in $name"}
 puts "UNIT SYNTHESIS $name DSP=$count"
 close_project
}
puts "ISOLATED UNIT RESOURCE COMPARISON PASSED"
