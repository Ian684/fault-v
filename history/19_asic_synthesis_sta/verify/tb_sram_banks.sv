`timescale 1ns/1ps
module tb_sram_banks;
 logic clk=0;always #20 clk=~clk;
 logic [3:0] done=0;
 for(genvar g=0;g<4;g++)begin:modes
  localparam bit ROM=g>=2;
  localparam logic [31:0] BASE=ROM?0:32'h10000000;
  logic rst=1,req_valid=0,req_write=0,rsp_ready=0,boot_valid=0;
  logic [31:0] req_addr=0,req_wdata=0,boot_addr=0,boot_wdata=0;
  logic [3:0] req_wstrb=0,boot_wstrb=15;
  wire req_ready,rsp_valid,rsp_err,boot_ready;
  wire [31:0] rsp_data,program_status;
  integer checks=0;
  logic [31:0] expected[0:4095];
  fault_v_memory #(.BASE_ADDR(BASE),.READ_ONLY(ROM),.WITH_STATUS(!ROM),.RESPONSE_DELAY((g%2)?7:1)) dut(.*);
  task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"SRAM mode=%0d %s",g,msg);checks++;endtask
  task automatic boot_write(input integer word_id,input logic [31:0] value);
   @(negedge clk);boot_valid=1;boot_addr=BASE+word_id*4;boot_wdata=value;
   @(posedge clk);must(boot_ready,"boot ready");@(negedge clk);boot_valid=0;
  endtask
  task automatic transaction(input logic write_en,input logic [31:0] addr,value,input logic [3:0] mask,input logic error_en,input logic [31:0] want,input integer stalls);
   @(negedge clk);req_valid=1;req_write=write_en;req_addr=addr;req_wdata=value;req_wstrb=mask;
   do @(posedge clk);while(!req_ready);
   @(negedge clk);req_valid=0;
   wait(rsp_valid);#1;must(rsp_err===error_en,"error flag");
   if(!write_en && !error_en)must(rsp_data===want,"read golden");
   repeat(stalls)begin @(posedge clk);#2;must(rsp_valid && rsp_err===error_en && (write_en || error_en || rsp_data===want),"held response");end
   @(negedge clk);rsp_ready=1;@(posedge clk);@(negedge clk);rsp_ready=0;
  endtask
  initial begin
   repeat(3)@(posedge clk);
   for(integer k=0;k<4096;k++)begin expected[k]=32'hc0de1000^(k*32'h10204081);boot_write(k,expected[k]);end
   @(negedge clk);rst=0;
   for(integer k=0;k<4096;k++)transaction(0,BASE+k*4,0,0,0,expected[k],k%17==0?3:0);
   for(integer bank=0;bank<8;bank++)begin
    for(integer lane=0;lane<4;lane++)begin
     transaction(1,BASE+bank*2048,32'h12345678,4'b0001<<lane,ROM,0,1);
     if(!ROM)expected[bank*512][lane*8+:8]=32'h12345678>>(lane*8);
     transaction(0,BASE+bank*2048,0,0,0,expected[bank*512],2);
    end
   end
   transaction(0,BASE+16384,0,0,1,0,2);transaction(0,BASE+1,0,0,1,0,1);
   if(!ROM)begin
    transaction(1,32'h20000000,32'h1234,15,0,0,0);transaction(0,32'h20000000,0,0,0,32'h1234,2);
    transaction(1,32'h20000000,1,1,1,0,0);
   end
   @(negedge clk);req_valid=1;req_write=0;req_addr=BASE;
   @(posedge clk);@(negedge clk);req_valid=0;rst=1;
   repeat(2)@(posedge clk);#1;must(!rsp_valid && !req_ready && program_status==0,"reset cancels control and status");
   @(negedge clk);rst=0;transaction(0,BASE,0,0,0,expected[0],0);
   $display("PASS SRAM mode=%0d checks=%0d words=4096 banks=8",g,checks);done[g]=1;
  end
 end
 initial begin wait(&done);$display("ALL 4 SRAM BANK MODES PASSED; 16384 WORD READS; BYTE MASKS, STALLS, ROM PROTECTION AND RESET");$finish;end
 initial begin #100000000;$fatal(1,"SRAM timeout");end
endmodule
