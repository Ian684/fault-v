open_hw_manager
connect_hw_server -url localhost:3121
set targets [get_hw_targets]
puts "FAULTV_HW_TARGET_COUNT=[llength $targets]"
foreach target $targets {puts "FAULTV_HW_TARGET=$target"}
if {[llength $targets] == 1} {
    current_hw_target [lindex $targets 0]
    open_hw_target
    foreach device [get_hw_devices] {
        puts "FAULTV_HW_DEVICE=$device PART=[get_property PART $device]"
    }
    close_hw_target
} elseif {[llength $targets] == 0} {
    puts "FAULTV_HW_NO_TARGET"
} else {
    puts "FAULTV_HW_MULTIPLE_TARGETS_SELECT_REQUIRED"
}
disconnect_hw_server
close_hw_manager
