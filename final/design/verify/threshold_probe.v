module threshold_probe(input clk,a,output y);
 sky130_fd_sc_hd__buf_8 driver(.A(a),.X(y));
 sky130_sram_2kbyte_1rw1r_32x512_8 sram0(.clk0(clk),.csb0(1'b0),.web0(1'b0),.wmask0({y,y,y,y}),.addr0(9'b0),.din0(32'b0),.clk1(clk),.csb1(1'b1),.addr1(9'b0));
 sky130_sram_2kbyte_1rw1r_32x512_8 sram1(.clk0(clk),.csb0(1'b0),.web0(1'b0),.wmask0({y,y,y,y}),.addr0(9'b0),.din0(32'b0),.clk1(clk),.csb1(1'b1),.addr1(9'b0));
 sky130_sram_2kbyte_1rw1r_32x512_8 sram2(.clk0(clk),.csb0(1'b0),.web0(1'b0),.wmask0({y,y,y,y}),.addr0(9'b0),.din0(32'b0),.clk1(clk),.csb1(1'b1),.addr1(9'b0));
 sky130_sram_2kbyte_1rw1r_32x512_8 sram3(.clk0(clk),.csb0(1'b0),.web0(1'b0),.wmask0({y,y,y,y}),.addr0(9'b0),.din0(32'b0),.clk1(clk),.csb1(1'b1),.addr1(9'b0));
 sky130_sram_2kbyte_1rw1r_32x512_8 sram4(.clk0(clk),.csb0(1'b0),.web0(1'b0),.wmask0({y,y,y,y}),.addr0(9'b0),.din0(32'b0),.clk1(clk),.csb1(1'b1),.addr1(9'b0));
 sky130_sram_2kbyte_1rw1r_32x512_8 sram5(.clk0(clk),.csb0(1'b0),.web0(1'b0),.wmask0({y,y,y,y}),.addr0(9'b0),.din0(32'b0),.clk1(clk),.csb1(1'b1),.addr1(9'b0));
 sky130_sram_2kbyte_1rw1r_32x512_8 sram6(.clk0(clk),.csb0(1'b0),.web0(1'b0),.wmask0({y,y,y,y}),.addr0(9'b0),.din0(32'b0),.clk1(clk),.csb1(1'b1),.addr1(9'b0));
 sky130_sram_2kbyte_1rw1r_32x512_8 sram7(.clk0(clk),.csb0(1'b0),.web0(1'b0),.wmask0({y,y,y,y}),.addr0(9'b0),.din0(32'b0),.clk1(clk),.csb1(1'b1),.addr1(9'b0));
endmodule
