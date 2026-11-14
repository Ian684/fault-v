module fault_v_payload(
    (* X_INTERFACE_INFO="xilinx.com:signal:clock:1.0 clk CLK", X_INTERFACE_PARAMETER="XIL_INTERFACENAME clk, FREQ_HZ 50000000, ASSOCIATED_RESET resetn" *)
    input wire clk,
    (* X_INTERFACE_INFO="xilinx.com:signal:reset:1.0 resetn RST", X_INTERFACE_PARAMETER="XIL_INTERFACENAME resetn, POLARITY ACTIVE_LOW" *)
    input wire resetn,
    input wire run,btn_reset,
    input wire [1:0] sw,
    output wire [3:0] led,
    output wire uart_tx,
    output wire [31:0] debug_status
);
    fault_v_payload_impl implementation(.clk(clk),.resetn(resetn),.run(run),
        .btn_reset(btn_reset),.sw(sw),.led(led),.uart_tx(uart_tx),.debug_status(debug_status));
endmodule
