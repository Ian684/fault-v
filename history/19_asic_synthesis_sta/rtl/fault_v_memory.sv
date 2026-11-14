`timescale 1ns/1ps
module fault_v_memory #(
 parameter logic [31:0] BASE_ADDR=32'h10000000,
 parameter integer WORDS=4096,
 parameter bit READ_ONLY=0,WITH_STATUS=0,
 parameter string INIT_FILE="",
 parameter integer RESPONSE_DELAY=1
)(
 input logic clk,rst,req_valid,req_write,
 output logic req_ready,
 input logic [31:0] req_addr,req_wdata,
 input logic [3:0] req_wstrb,
 output logic rsp_valid,
 input logic rsp_ready,
 output logic [31:0] rsp_data,
 output logic rsp_err,
 output logic [31:0] program_status,
 input logic boot_valid,
 input logic [31:0] boot_addr,boot_wdata,
 input logic [3:0] boot_wstrb,
 output logic boot_ready
);
 localparam integer BANKS=WORDS/512;
 localparam integer BANK_BITS=$clog2(BANKS);
 logic busy,read_pending;
 integer remaining;
 logic [BANK_BITS-1:0] read_bank;
 wire [31:0] word_index=(req_addr-BASE_ADDR)>>2;
 wire [31:0] boot_index=(boot_addr-BASE_ADDR)>>2;
 wire ram_hit=req_addr>=BASE_ADDR && word_index<WORDS && req_addr[1:0]==0;
 wire boot_hit=boot_addr>=BASE_ADDR && boot_index<WORDS && boot_addr[1:0]==0;
 wire status_hit=WITH_STATUS && req_addr==32'h20000000;
 wire request_fire=req_valid && req_ready;
 wire ram_fire=request_fire && ram_hit && !(req_write && READ_ONLY);
 wire boot_fire=boot_valid && boot_ready;
 wire [BANKS-1:0][31:0] bank_data;
 assign boot_ready=!busy && !rsp_valid && boot_hit;
 assign req_ready=!rst && !busy && !rsp_valid && !boot_valid;
 for(genvar k=0;k<BANKS;k++)begin:banks
  wire selected=boot_fire?(boot_index>>9)==k:ram_fire && (word_index>>9)==k;
  wire [8:0] address=boot_fire?boot_index[8:0]:word_index[8:0];
  wire write_enable=boot_fire || req_write;
  sky130_sram_2kbyte_1rw1r_32x512_8 u_sram(
   .clk0(clk),.csb0(!selected),.web0(!write_enable),
   .wmask0(boot_fire?boot_wstrb:req_wstrb),.addr0(address),
   .din0(boot_fire?boot_wdata:req_wdata),.dout0(bank_data[k]),
   .clk1(clk),.csb1(1'b1),.addr1(9'b0),.dout1()
  );
 end
 always_ff @(posedge clk)begin
  if(rst)begin
   busy<=0;remaining<=0;read_pending<=0;read_bank<=0;
   rsp_valid<=0;rsp_err<=0;rsp_data<=0;program_status<=0;
  end else begin
   if(rsp_valid && rsp_ready)rsp_valid<=0;
   // OpenRAM captures at the rising edge and produces data after the falling edge.
   if(read_pending)begin rsp_data<=bank_data[read_bank];read_pending<=0;end
   if(request_fire)begin
    busy<=1;remaining<=(RESPONSE_DELAY<1)?1:RESPONSE_DELAY;
    rsp_data<=0;rsp_err<=0;
    if(ram_hit)begin
     if(req_write && READ_ONLY)rsp_err<=1;
     else if(!req_write)begin read_pending<=1;read_bank<=word_index[9+:BANK_BITS];end
    end else if(status_hit)begin
     if(req_write && req_wstrb!=4'hf)rsp_err<=1;
     else begin rsp_data<=program_status;if(req_write)program_status<=req_wdata;end
    end else rsp_err<=1;
   end
   if(busy)begin
    if(remaining<=1)begin busy<=0;rsp_valid<=1;end
    else remaining<=remaining-1;
   end
  end
 end
endmodule
