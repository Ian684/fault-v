`timescale 1ns/1ps
module fault_v_clock(input wire clk125, output wire clk, output wire locked);
    wire input_clock, feedback_raw, feedback, clock_raw;
    IBUF u_ibuf(.I(clk125), .O(input_clock));
    MMCME2_BASE #(
        .BANDWIDTH("OPTIMIZED"), .CLKIN1_PERIOD(8.0),
        .DIVCLK_DIVIDE(1), .CLKFBOUT_MULT_F(8.0),
        .CLKOUT0_DIVIDE_F(40.0), .STARTUP_WAIT("FALSE")
    ) u_mmcm (
        .CLKIN1(input_clock), .CLKFBIN(feedback), .RST(1'b0), .PWRDWN(1'b0),
        .CLKFBOUT(feedback_raw), .CLKOUT0(clock_raw), .LOCKED(locked),
        .CLKFBOUTB(), .CLKOUT0B(), .CLKOUT1(), .CLKOUT1B(),
        .CLKOUT2(), .CLKOUT2B(), .CLKOUT3(), .CLKOUT3B(),
        .CLKOUT4(), .CLKOUT5(), .CLKOUT6()
    );
    BUFG u_feedback(.I(feedback_raw), .O(feedback));
    BUFG u_clock(.I(clock_raw), .O(clk));
endmodule
