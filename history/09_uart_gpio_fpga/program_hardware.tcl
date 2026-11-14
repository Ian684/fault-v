set bitfile [file normalize build/fault_v_fpga_top.bit]
if {![file exists $bitfile]} {error "Missing bitstream"}
open_hw_manager
connect_hw_server -url localhost:3121
set targets [get_hw_targets -quiet *1234-tulA]
if {[llength $targets] != 1} {error "Expected verified Z2 JTAG target not uniquely present"}
current_hw_target [lindex $targets 0]
open_hw_target
set devices [get_hw_devices -quiet xc7z020_1]
if {[llength $devices] != 1} {error "Expected xc7z020_1 not uniquely present"}
set device [lindex $devices 0]
if {[get_property PART $device] ne "xc7z020"} {error "Unexpected FPGA part"}
current_hw_device $device
set_property PROGRAM.FILE $bitfile $device
puts "FAULTV_PROGRAM_FILE=$bitfile"
program_hw_devices $device
refresh_hw_device $device
puts "FAULTV_PROGRAM_COMPLETED device=$device part=[get_property PART $device]"
if {[lsearch -exact [list_property $device] REGISTER.CONFIG_STATUS] >= 0} {
    puts "FAULTV_CONFIG_STATUS=[get_property REGISTER.CONFIG_STATUS $device]"
}
close_hw_target
disconnect_hw_server
close_hw_manager
