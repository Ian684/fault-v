set_property PACKAGE_PIN H16 [get_ports clk125]
set_property IOSTANDARD LVCMOS33 [get_ports clk125]
create_clock -name board_clk125 -period 8.000 [get_ports clk125]
set_property PACKAGE_PIN D19 [get_ports btn_reset]
set_property IOSTANDARD LVCMOS33 [get_ports btn_reset]
set_property PACKAGE_PIN R14 [get_ports {led[0]}]
set_property PACKAGE_PIN P14 [get_ports {led[1]}]
set_property PACKAGE_PIN N16 [get_ports {led[2]}]
set_property PACKAGE_PIN M14 [get_ports {led[3]}]
set_property IOSTANDARD LVCMOS33 [get_ports {led[*]}]
# Button feeds asynchronous reset assertion only. Release is synchronized.
set_false_path -from [get_ports btn_reset]
# LEDs have no external clocked receiving device; internal paths stay timed.
set_false_path -to [get_ports {led[*]}]
