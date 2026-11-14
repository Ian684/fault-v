`timescale 1ns/1ps
module fault_v_payload_impl(
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 clk CLK", X_INTERFACE_PARAMETER="XIL_INTERFACENAME clk, FREQ_HZ 50000000, ASSOCIATED_RESET resetn" *)
    input wire clk,
    (* X_INTERFACE_INFO="xilinx.com:signal:reset:1.0 resetn RST", X_INTERFACE_PARAMETER="XIL_INTERFACENAME resetn, POLARITY ACTIVE_LOW" *)
    input wire resetn,
    input wire run,
    input wire btn_reset,
    input wire [1:0] sw,
    output wire [3:0] led,
    output wire uart_tx,
    output wire [31:0] debug_status
);
    logic rst=1'b1;
    wire base_reset;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) logic [1:0] sw_meta=0,sw_sync=0;
    always_ff @(posedge clk)
        if(rst) begin sw_meta<=0;sw_sync<=0;end
        else begin sw_meta<=sw;sw_sync<=sw_meta;end
    fault_v_reset #(.HOLD_BITS(18)) u_reset(.clk(clk),.locked(resetn),.btn_reset(btn_reset),.rst(base_reset));
    always_ff @(posedge clk) rst<=base_reset || !resetn || !run;
    wire halted;
    wire [31:0] program_status;
    fault_v_pkg::halt_cause_t halt_cause;
    assign debug_status={16'b0,halt_cause,6'b0,halted,program_status[1:0]};
    fault_v_soc #(.IMEM_FILE("stream_demo.mem"),.UART_CLKS_PER_BIT(434)) u_soc(
        .clk(clk),.rst(rst),.gpio_in(sw_sync),.gpio_out(led),.uart_tx(uart_tx),
        .program_status(program_status),.halted(halted),.halt_cause(halt_cause),
        .fault_pc(),.fault_addr(),.pc(),.state(),.retire_valid(),.retire_rd_we(),
        .retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
endmodule
