set_param general.maxThreads 2
create_project fault_v_extension_c build/project -part xc7z020clg400-1 -force
set_property target_language Verilog [current_project]
add_files rtl/fault_v_pkg.sv
foreach f [glob rtl/*.sv] {if {[file tail $f] ne "fault_v_pkg.sv"} {add_files $f}}
add_files [glob board/*.sv]
add_files [glob board/*.v]
add_files programs/stream_demo.mem
add_files -fileset constrs_1 constraints/pynq_network.xdc
update_compile_order -fileset sources_1
create_bd_design network
set ps [create_bd_cell -type ip -vlnv xilinx.com:ip:processing_system7:5.5 ps7]
source ps_preset.tcl
set filtered {}
set props [list_property $ps]
foreach {key value} $ps_preset {
    if {[lsearch -exact $props $key]>=0 && ![regexp {CONFIG.PCW_[MS]_AXI_.*_FREQMHZ|CONFIG.PCW_NUM_F2P_INTR_INPUTS} $key]} {lappend filtered $key $value}
}
set_property -dict $filtered $ps
set_property -dict [list CONFIG.PCW_USE_M_AXI_GP0 1 CONFIG.PCW_USE_M_AXI_GP1 0 CONFIG.PCW_USE_S_AXI_GP0 0 CONFIG.PCW_USE_S_AXI_GP1 0 CONFIG.PCW_USE_S_AXI_HP0 0 CONFIG.PCW_USE_S_AXI_HP1 0 CONFIG.PCW_USE_S_AXI_HP2 0 CONFIG.PCW_USE_S_AXI_HP3 0 CONFIG.PCW_USE_S_AXI_ACP 0 CONFIG.PCW_FPGA0_PERIPHERAL_FREQMHZ 50.000000 CONFIG.PCW_EN_CLK0_PORT 1 CONFIG.PCW_EN_RST0_PORT 1] $ps
make_bd_intf_pins_external [get_bd_intf_pins ps7/DDR]
make_bd_intf_pins_external [get_bd_intf_pins ps7/FIXED_IO]
set fabric [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_interconnect:2.1 axi_bus]
set_property CONFIG.NUM_MI 2 $fabric
set rx [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_uartlite:2.0 serial_rx]
set_property -dict [list CONFIG.C_S_AXI_ACLK_FREQ_HZ_d 50 CONFIG.C_BAUDRATE 115200 CONFIG.C_DATA_BITS 8 CONFIG.C_USE_PARITY 0] $rx
set ctl [create_bd_cell -type ip -vlnv xilinx.com:ip:axi_gpio:2.0 control]
set_property -dict [list CONFIG.C_GPIO_WIDTH 1 CONFIG.C_ALL_OUTPUTS 1 CONFIG.C_DOUT_DEFAULT 0x00000000 CONFIG.C_IS_DUAL 1 CONFIG.C_GPIO2_WIDTH 32 CONFIG.C_ALL_INPUTS_2 1] $ctl
set reset [create_bd_cell -type ip -vlnv xilinx.com:ip:proc_sys_reset:5.0 fabric_reset]
set one [create_bd_cell -type ip -vlnv xilinx.com:ip:xlconstant:1.1 constant_one]
set_property CONFIG.CONST_VAL 1 $one
set core [create_bd_cell -type module -reference fault_v_payload fault_v]
connect_bd_intf_net [get_bd_intf_pins ps7/M_AXI_GP0] [get_bd_intf_pins axi_bus/S00_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_bus/M00_AXI] [get_bd_intf_pins serial_rx/S_AXI]
connect_bd_intf_net [get_bd_intf_pins axi_bus/M01_AXI] [get_bd_intf_pins control/S_AXI]
connect_bd_net [get_bd_pins ps7/FCLK_CLK0] [get_bd_pins ps7/M_AXI_GP0_ACLK] [get_bd_pins axi_bus/ACLK] [get_bd_pins axi_bus/S00_ACLK] [get_bd_pins axi_bus/M00_ACLK] [get_bd_pins axi_bus/M01_ACLK] [get_bd_pins serial_rx/s_axi_aclk] [get_bd_pins control/s_axi_aclk] [get_bd_pins fabric_reset/slowest_sync_clk] [get_bd_pins fault_v/clk]
connect_bd_net [get_bd_pins ps7/FCLK_RESET0_N] [get_bd_pins fabric_reset/ext_reset_in]
connect_bd_net [get_bd_pins constant_one/dout] [get_bd_pins fabric_reset/dcm_locked]
connect_bd_net [get_bd_pins fabric_reset/interconnect_aresetn] [get_bd_pins axi_bus/ARESETN]
connect_bd_net [get_bd_pins fabric_reset/peripheral_aresetn] [get_bd_pins axi_bus/S00_ARESETN] [get_bd_pins axi_bus/M00_ARESETN] [get_bd_pins axi_bus/M01_ARESETN] [get_bd_pins serial_rx/s_axi_aresetn] [get_bd_pins control/s_axi_aresetn] [get_bd_pins fault_v/resetn]
connect_bd_net [get_bd_pins control/gpio_io_o] [get_bd_pins fault_v/run]
connect_bd_net [get_bd_pins fault_v/debug_status] [get_bd_pins control/gpio2_io_i]
connect_bd_net [get_bd_pins fault_v/uart_tx] [get_bd_pins serial_rx/rx]
create_bd_port -dir I btn_reset
create_bd_port -dir I -from 1 -to 0 sw
create_bd_port -dir O -from 3 -to 0 led
create_bd_port -dir O uart_tx
foreach pin {btn_reset sw led uart_tx} {connect_bd_net [get_bd_pins fault_v/$pin] [get_bd_ports $pin]}
assign_bd_address -offset 0x42C00000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs serial_rx/S_AXI/Reg]
assign_bd_address -offset 0x41200000 -range 64K -target_address_space [get_bd_addr_spaces ps7/Data] [get_bd_addr_segs control/S_AXI/Reg]
validate_bd_design
set_property CONFIG.C_BAUDRATE 115200 $rx
validate_bd_design
if {[get_property CONFIG.C_BAUDRATE $rx] != 115200} {error "UART baud rate changed"}
save_bd_design
generate_target all [get_files network.bd]
make_wrapper -files [get_files network.bd] -top
add_files build/project/fault_v_extension_c.gen/sources_1/bd/network/hdl/network_wrapper.v
set_property top network_wrapper [current_fileset]
update_compile_order -fileset sources_1
