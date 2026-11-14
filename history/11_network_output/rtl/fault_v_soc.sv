`timescale 1ns/1ps
module fault_v_soc #(
    parameter string IMEM_FILE="",
    parameter integer IMEM_DELAY=1,
    parameter integer DMEM_DELAY=1,
    parameter integer UART_CLKS_PER_BIT=217
) (
    input logic clk,rst,
    input logic [1:0] gpio_in,
    output logic [3:0] gpio_out,
    output logic uart_tx,
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
    logic bus_pending,selected_io;
    logic ram_req_ready,ram_rsp_valid,ram_rsp_err,ram_rsp_ready;
    logic io_req_ready,io_rsp_valid,io_rsp_err,io_rsp_ready;
    logic [31:0] ram_rsp_data,io_rsp_data;
    wire io_hit=(dmem_req_addr[31:4]==28'h2000010) || (dmem_req_addr[31:4]==28'h2000020);
    wire ram_req_valid=dmem_req_valid && !bus_pending && !io_hit;
    wire io_req_valid=dmem_req_valid && !bus_pending && io_hit;
    assign dmem_req_ready=!rst && !bus_pending && (io_hit ? io_req_ready : ram_req_ready);
    assign dmem_rsp_valid=!rst && bus_pending && (selected_io ? io_rsp_valid : ram_rsp_valid);
    assign dmem_rsp_data=selected_io ? io_rsp_data : ram_rsp_data;
    assign dmem_rsp_err=selected_io ? io_rsp_err : ram_rsp_err;
    assign ram_rsp_ready=!rst && bus_pending && !selected_io && dmem_rsp_ready;
    assign io_rsp_ready=!rst && bus_pending && selected_io && dmem_rsp_ready;
    always_ff @(posedge clk)
        if(rst) begin bus_pending<=0;selected_io<=0;end
        else begin
            if(dmem_req_valid && dmem_req_ready) begin bus_pending<=1;selected_io<=io_hit;end
            if(dmem_rsp_valid && dmem_rsp_ready) bus_pending<=0;
        end
    fault_v_cpu u_cpu(.*);
    fault_v_memory #(.BASE_ADDR(0),.READ_ONLY(1),.INIT_FILE(IMEM_FILE),.RESPONSE_DELAY(IMEM_DELAY)) u_imem(
        .clk(clk),.rst(rst),.req_valid(imem_req_valid),.req_ready(imem_req_ready),
        .req_write(1'b0),.req_addr(imem_req_addr),.req_wdata(32'b0),.req_wstrb(4'b0),
        .rsp_valid(imem_rsp_valid),.rsp_ready(imem_rsp_ready),.rsp_data(imem_rsp_data),
        .rsp_err(imem_rsp_err),.program_status(unused_status));
    fault_v_memory #(.BASE_ADDR(32'h10000000),.WITH_STATUS(1),.RESPONSE_DELAY(DMEM_DELAY)) u_dmem(
        .clk(clk),.rst(rst),.req_valid(ram_req_valid),.req_ready(ram_req_ready),
        .req_write(dmem_req_write),.req_addr(dmem_req_addr),.req_wdata(dmem_req_wdata),.req_wstrb(dmem_req_wstrb),
        .rsp_valid(ram_rsp_valid),.rsp_ready(ram_rsp_ready),.rsp_data(ram_rsp_data),
        .rsp_err(ram_rsp_err),.program_status(program_status));
    fault_v_io #(.UART_CLKS_PER_BIT(UART_CLKS_PER_BIT)) u_io(
        .clk(clk),.rst(rst),.req_valid(io_req_valid),.req_ready(io_req_ready),
        .req_write(dmem_req_write),.req_addr(dmem_req_addr),.req_wdata(dmem_req_wdata),.req_wstrb(dmem_req_wstrb),
        .rsp_valid(io_rsp_valid),.rsp_ready(io_rsp_ready),.rsp_data(io_rsp_data),.rsp_err(io_rsp_err),
        .gpio_in(gpio_in),.gpio_out(gpio_out),.uart_tx(uart_tx));
endmodule
