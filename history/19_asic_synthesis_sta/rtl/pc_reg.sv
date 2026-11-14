`timescale 1ns/1ps
module pc_reg (
    input  logic        clk,
    input  logic        rst,
    input  logic        pc_we,
    input  logic [31:0] pc_next,

    output logic [31:0] pc
);

    always_ff @(posedge clk) begin
        if (rst)
            pc <= 32'h00000000;
        else if (pc_we)
            pc <= pc_next;
    end

endmodule
