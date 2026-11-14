`timescale 1ns/1ps
module fault_v_soc #(
    parameter string IMEM_FILE="",
    parameter integer IMEM_DELAY=1,
    parameter integer DMEM_DELAY=1
) (
    input logic clk,rst,
    output logic [31:0] program_status,
    output logic halted,
    output fault_v_pkg::halt_cause_t halt_cause,
    output logic [31:0] fault_pc,fault_addr,pc,
    output fault_v_pkg::cpu_state_t state,
    output logic retire_valid,retire_rd_we,
    output logic [31:0] retire_pc,retire_instruction,retire_rd_data,
    output logic [4:0] retire_rd_addr
);
    logic imem_req_valid,imem_req_ready,imem_rsp_valid,imem_rsp_err,imem_rsp_ready;
    logic [31:0] imem_req_addr,imem_rsp_data;
    logic dmem_req_valid,dmem_req_ready,dmem_req_write,dmem_rsp_valid,dmem_rsp_err,dmem_rsp_ready;
    logic [31:0] dmem_req_addr,dmem_req_wdata,dmem_rsp_data;
    logic [3:0] dmem_req_wstrb;
    logic [31:0] unused_status;
    fault_v_cpu u_cpu(.*);
    fault_v_memory #(.BASE_ADDR(0),.READ_ONLY(1),.INIT_FILE(IMEM_FILE),.RESPONSE_DELAY(IMEM_DELAY)) u_imem(
        .clk(clk),.rst(rst),.req_valid(imem_req_valid),.req_ready(imem_req_ready),
        .req_write(1'b0),.req_addr(imem_req_addr),.req_wdata(32'b0),.req_wstrb(4'b0),
        .rsp_valid(imem_rsp_valid),.rsp_ready(imem_rsp_ready),.rsp_data(imem_rsp_data),
        .rsp_err(imem_rsp_err),.program_status(unused_status));
    fault_v_memory #(.BASE_ADDR(32'h10000000),.WITH_STATUS(1),.RESPONSE_DELAY(DMEM_DELAY)) u_dmem(
        .clk(clk),.rst(rst),.req_valid(dmem_req_valid),.req_ready(dmem_req_ready),
        .req_write(dmem_req_write),.req_addr(dmem_req_addr),.req_wdata(dmem_req_wdata),.req_wstrb(dmem_req_wstrb),
        .rsp_valid(dmem_rsp_valid),.rsp_ready(dmem_rsp_ready),.rsp_data(dmem_rsp_data),
        .rsp_err(dmem_rsp_err),.program_status(program_status));
endmodule
