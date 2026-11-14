set_property PACKAGE_PIN H16 [get_ports clk125]
set_property IOSTANDARD LVCMOS33 [get_ports clk125]
create_clock -name board_clk125 -period 8.000 [get_ports clk125]
set_property PACKAGE_PIN D19 [get_ports btn_reset]
set_property PACKAGE_PIN M20 [get_ports {sw[0]}]
set_property PACKAGE_PIN M19 [get_ports {sw[1]}]
set_property PACKAGE_PIN R14 [get_ports {led[0]}]
set_property PACKAGE_PIN P14 [get_ports {led[1]}]
set_property PACKAGE_PIN N16 [get_ports {led[2]}]
set_property PACKAGE_PIN M14 [get_ports {led[3]}]
# Pmod B pin 1: PL UART TX, connect to 3.3V USB-UART RX.
set_property PACKAGE_PIN W14 [get_ports uart_tx]
set_property IOSTANDARD LVCMOS33 [get_ports {btn_reset sw[*] led[*] uart_tx}]
set_false_path -from [get_ports btn_reset]
# Only first stages are asynchronous. Second-stage paths remain timed.
set sw_first_stage [get_pins -filter {REF_PIN_NAME == D} -of_objects [get_cells -hier -filter {NAME =~ *sw_meta_reg*}]]
set_false_path -from [get_ports {sw[*]}] -to $sw_first_stage
# LEDs and asynchronous UART receiver have no external shared capture clock.
set_false_path -to [get_ports {led[*] uart_tx}]
