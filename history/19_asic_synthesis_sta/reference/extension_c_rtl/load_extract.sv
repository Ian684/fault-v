`timescale 1ns/1ps
module load_extract (
    input logic [31:0] word_data,
    input logic [1:0] byte_offset,
    input fault_v_pkg::mem_size_t mem_size,
    input logic load_unsigned,
    output logic [31:0] result
);
    import fault_v_pkg::*;
    logic [31:0] shifted;
    always_comb begin
        shifted=word_data >> {byte_offset,3'b000};
        result=32'b0;
        case (mem_size)
            MEM_BYTE: result=load_unsigned?{24'b0,shifted[7:0]}:{{24{shifted[7]}},shifted[7:0]};
            MEM_HALF: result=load_unsigned?{16'b0,shifted[15:0]}:{{16{shifted[15]}},shifted[15:0]};
            MEM_WORD: result=word_data;
            default: result=32'b0;
        endcase
    end
endmodule
