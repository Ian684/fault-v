`timescale 1ns/1ps
module store_align (
    input logic [31:0] data,
    input logic [1:0] byte_offset,
    input fault_v_pkg::mem_size_t mem_size,
    output logic [31:0] wdata,
    output logic [3:0] wstrb
);
    import fault_v_pkg::*;
    always_comb begin
        wdata=32'b0; wstrb=4'b0;
        case (mem_size)
            MEM_BYTE: begin
                wdata={24'b0,data[7:0]} << {byte_offset,3'b000};
                wstrb=4'b0001 << byte_offset;
            end
            MEM_HALF: begin
                if (!byte_offset[0]) begin
                    wdata={16'b0,data[15:0]} << {byte_offset,3'b000};
                    wstrb=4'b0011 << byte_offset;
                end
            end
            MEM_WORD: begin
                if (byte_offset==0) begin wdata=data; wstrb=4'b1111; end
            end
            default: begin end
        endcase
    end
endmodule
