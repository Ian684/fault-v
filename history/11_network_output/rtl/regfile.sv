`timescale 1ns/1ps
module regfile (
    input  logic        clk,
    input  logic        rst,

    input  logic [4:0]  rs1_addr,
    input  logic [4:0]  rs2_addr,
    output logic [31:0] rs1_data,
    output logic [31:0] rs2_data,

    input  logic        rd_we,
    input  logic [4:0]  rd_addr,
    input  logic [31:0] rd_data
);

    logic [31:0] regs [0:31];

    // 同步 Reset 與同步寫入
    always_ff @(posedge clk) begin
        if (rst) begin
            for (int i = 0; i < 32; i++) begin
                regs[i] <= 32'b0;
            end
        end
        else if (rd_we && (rd_addr != 5'd0)) begin
            regs[rd_addr] <= rd_data;
        end
    end

    // 兩個組合讀取埠
    assign rs1_data =
        (rs1_addr == 5'd0) ? 32'b0 : regs[rs1_addr];

    assign rs2_data =
        (rs2_addr == 5'd0) ? 32'b0 : regs[rs2_addr];

endmodule
