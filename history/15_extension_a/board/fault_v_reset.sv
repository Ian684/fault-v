`timescale 1ns/1ps
module fault_v_reset #(parameter integer HOLD_BITS=18)(
    input wire clk, input wire locked, input wire btn_reset, output logic rst=1'b1
);
    // Asynchronous assertion; three clock edges synchronize release.
    // Every button bounce restarts the release delay (2^18 cycles: 10.49 ms at 25 MHz, 5.24 ms at 50 MHz).
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) logic [2:0] button_pipe=3'b111;
    (* ASYNC_REG="TRUE", SHREG_EXTRACT="NO" *) logic [2:0] lock_pipe=3'b111;
    logic [HOLD_BITS-1:0] release_count='0;
    always_ff @(posedge clk or posedge btn_reset)
        if (btn_reset) button_pipe<=3'b111;
        else button_pipe<={button_pipe[1:0],1'b0};
    always_ff @(posedge clk or negedge locked)
        if (!locked) lock_pipe<=3'b111;
        else lock_pipe<={lock_pipe[1:0],1'b0};
    // A final synchronous register prevents asynchronous reset changes from
    // reaching BRAM enable pins between clock edges.
    always_ff @(posedge clk) begin
        if (button_pipe[2] || lock_pipe[2]) begin
            release_count<='0;
            rst<=1;
        end else begin
            if (!(&release_count)) release_count<=release_count+1'b1;
            rst<=!(&release_count);
        end
    end
endmodule

