`timescale 1ns/1ps
module fault_v_memory #(
    parameter logic [31:0] BASE_ADDR=32'h10000000,
    parameter integer WORDS=4096,
    parameter bit READ_ONLY=0,
    parameter bit WITH_STATUS=0,
    parameter string INIT_FILE="",
    parameter integer RESPONSE_DELAY=1
) (
    input logic clk,rst,
    input logic req_valid,
    output logic req_ready,
    input logic req_write,
    input logic [31:0] req_addr,req_wdata,
    input logic [3:0] req_wstrb,
    output logic rsp_valid,
    input logic rsp_ready,
    output logic [31:0] rsp_data,
    output logic rsp_err,
    output logic [31:0] program_status
);
    (* ram_style="block" *) logic [31:0] mem[0:WORDS-1];
    logic [31:0] ram_data,other_data;
    logic response_is_ram;
    logic busy;
    integer remaining;
    logic ram_hit,status_hit;
    logic [31:0] word_index;
    initial begin
        for (integer i=0;i<WORDS;i=i+1) mem[i]=0;
        if (INIT_FILE!="") $readmemh(INIT_FILE,mem);
    end
    assign word_index=(req_addr-BASE_ADDR)>>2;
    assign ram_hit=(req_addr>=BASE_ADDR) && (word_index<WORDS) && (req_addr[1:0]==0);
    assign status_hit=WITH_STATUS && (req_addr==32'h20000000);
    assign req_ready=!rst && !busy && !rsp_valid;
    assign rsp_data=response_is_ram ? ram_data : other_data;
    // BRAM read register has no reset or non-RAM data input.
    // Selector and protocol registers supply reset/status/error behavior.
    always_ff @(posedge clk) begin
        if (!rst && req_valid && req_ready && ram_hit && !(req_write && READ_ONLY)) begin
            ram_data<=mem[word_index];
            if (req_write && !READ_ONLY)
                for (integer lane=0;lane<4;lane=lane+1)
                    if (req_wstrb[lane]) mem[word_index][lane*8 +: 8]<=req_wdata[lane*8 +: 8];
        end
    end
    always_ff @(posedge clk) begin
        if (rst) begin
            busy<=0; remaining<=0; rsp_valid<=0; other_data<=0; response_is_ram<=0; rsp_err<=0;
            program_status<=0;
            // RAM contents intentionally survive reset. Accepted writes are not undone.
        end else begin
            if (req_valid && req_ready) begin
                busy<=1; remaining<=(RESPONSE_DELAY<1)?1:RESPONSE_DELAY;
                other_data<=0; response_is_ram<=0; rsp_err<=0;
                if (ram_hit) begin
                    if (req_write && READ_ONLY) rsp_err<=1;
                    else response_is_ram<=1;
                end else if (status_hit) begin
                    if (req_write && (req_wstrb!=4'b1111)) rsp_err<=1;
                    else begin
                        other_data<=program_status;
                        if (req_write) program_status<=req_wdata;
                    end
                end else rsp_err<=1;
            end
            if (busy) begin
                if (remaining<=1) begin busy<=0; rsp_valid<=1; end
                else remaining<=remaining-1;
            end
            if (rsp_valid && rsp_ready) rsp_valid<=0;
        end
    end
endmodule
