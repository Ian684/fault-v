`timescale 1ns/1ps
module fault_v_fpga_top #(
    parameter string IMEM_FILE="board_loop.mem",
    parameter integer RESET_HOLD_BITS=18,
    parameter integer UART_CLKS_PER_BIT=217
)(input wire clk125,btn_reset, input wire [1:0] sw,
  output wire [3:0] led,output wire uart_tx);
    wire clk,locked,rst;
    (* ASYNC_REG="TRUE",SHREG_EXTRACT="NO" *) logic [1:0] sw_meta=0,sw_sync=0;
    always_ff @(posedge clk)
        if(rst) begin sw_meta<=0;sw_sync<=0;end
        else begin sw_meta<=sw;sw_sync<=sw_meta;end
    fault_v_clock u_clock(.clk125(clk125),.clk(clk),.locked(locked));
    fault_v_reset #(.HOLD_BITS(RESET_HOLD_BITS)) u_reset(.*);
    fault_v_soc #(.IMEM_FILE(IMEM_FILE),.UART_CLKS_PER_BIT(UART_CLKS_PER_BIT)) u_soc(
        .clk(clk),.rst(rst),.gpio_in(sw_sync),.gpio_out(led),.uart_tx(uart_tx),
        .program_status(),.halted(),.halt_cause(),.fault_pc(),.fault_addr(),.pc(),.state(),
        .retire_valid(),.retire_rd_we(),.retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
endmodule
