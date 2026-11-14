`timescale 1ns/1ps
module fault_v_asic_top #(parameter integer UART_CLKS_PER_BIT=217, BOOT_TIMEOUT_CLKS=25000000)(
 input logic clk,reset_n,uart_rx,
 input logic [1:0] gpio_in,
 output logic uart_tx,running,boot_error,
 output logic [3:0] gpio_out,
 output logic [31:0] debug_status,fault_pc,fault_addr
);
 logic [2:0] reset_pipe;
 always_ff @(posedge clk or negedge reset_n)
  if(!reset_n)reset_pipe<=3'b111;else reset_pipe<={reset_pipe[1:0],1'b0};
 wire system_reset=reset_pipe[2];
 wire core_reset=system_reset || !running;
 logic [1:0] gpio_meta,gpio_sync;
 always_ff @(posedge clk)if(system_reset)begin gpio_meta<=0;gpio_sync<=0;end
  else begin gpio_meta<=gpio_in;gpio_sync<=gpio_meta;end
 wire boot_valid,boot_ready;
 wire [31:0] boot_addr,boot_wdata;
 wire [3:0] boot_wstrb;
 fault_v_loader #(.CLKS_PER_BIT(UART_CLKS_PER_BIT),.TIMEOUT_CLKS(BOOT_TIMEOUT_CLKS)) u_loader(
  .clk(clk),.rst(system_reset),.rx(uart_rx),.running(running),.boot_error(boot_error),
  .boot_valid(boot_valid),.boot_addr(boot_addr),.boot_wdata(boot_wdata),.boot_wstrb(boot_wstrb),.boot_ready(boot_ready));
 wire halted;
 wire [31:0] program_status;
 fault_v_pkg::halt_cause_t halt_cause;
 assign debug_status={19'b0,halt_cause,6'b0,halted,program_status[1:0]};
 fault_v_soc #(.UART_CLKS_PER_BIT(UART_CLKS_PER_BIT)) u_soc(
  .clk(clk),.rst(core_reset),.boot_valid(boot_valid),.boot_addr(boot_addr),.boot_wdata(boot_wdata),
  .boot_wstrb(boot_wstrb),.boot_ready(boot_ready),.gpio_in(gpio_sync),.gpio_out(gpio_out),.uart_tx(uart_tx),
  .halted(halted),.halt_cause(halt_cause),.program_status(program_status),.fault_pc(fault_pc),.fault_addr(fault_addr),
  .pc(),.state(),.retire_valid(),.retire_rd_we(),.retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
endmodule
