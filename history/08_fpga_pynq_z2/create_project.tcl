# Launch from package root in Vivado Tcl Console.
create_project fault_v_z2 build/project -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
add_files rtl/fault_v_pkg.sv
foreach f [glob rtl/*.sv] {
    if {[file tail $f] ne "fault_v_pkg.sv"} {add_files $f}
}
add_files [glob board/*.sv]
add_files programs/integration.mem
add_files -fileset constrs_1 constraints/pynq_z2.xdc
set_property top fault_v_fpga_top [current_fileset]
update_compile_order -fileset sources_1
