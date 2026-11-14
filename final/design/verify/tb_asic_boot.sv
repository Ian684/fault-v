`timescale 1ns/1ps
module tb_asic_boot;
 logic clk=0;always #20 clk=~clk;
 logic reset_n=0,uart_rx=1;
 logic [1:0] gpio_in=0;
 wire uart_tx,running,boot_error;wire [3:0] gpio_out;wire [31:0] debug_status,fault_pc,fault_addr;
 fault_v_asic_top #(.UART_CLKS_PER_BIT(8),.BOOT_TIMEOUT_CLKS(2000)) dut(.*);
 logic [31:0] image[0:4095];
 integer bytes=0,checks=0;string text="C OK";
 function automatic logic [31:0] crc_byte(input logic [31:0] crc,input logic [7:0] value);
  logic [31:0] c;c=crc^{24'b0,value};
  for(integer i=0;i<8;i++)c=c[0]?(c>>1)^32'hedb88320:c>>1;
  return c;
 endfunction
 task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"BOOT %s debug=%h fault=%h",msg,debug_status,fault_pc);checks++;endtask
 task automatic send_byte(input logic [7:0] value,input logic bad_stop=0);
  @(negedge clk);uart_rx=0;repeat(8)@(negedge clk);
  for(integer b=0;b<8;b++)begin uart_rx=value[b];repeat(8)@(negedge clk);end
  uart_rx=!bad_stop;repeat(8)@(negedge clk);uart_rx=1;repeat(2)@(negedge clk);
 endtask
 task automatic header(input integer words);
  send_byte(8'h46);send_byte(8'h56);send_byte(1);send_byte(0);send_byte(words&255);send_byte((words>>8)&255);
 endtask
 task automatic frame(input integer count,input logic corrupt);
  logic [31:0] crc;crc=32'hffffffff;header(count);
  for(integer k=0;k<count;k++)for(integer b=0;b<4;b++)begin send_byte(image[k]>>(b*8));crc=crc_byte(crc,image[k]>>(b*8));end
  crc=~crc;if(corrupt)crc=crc^1;
  for(integer b=0;b<4;b++)send_byte(crc>>(b*8));
  repeat(10)@(posedge clk);
 endtask
 task automatic reset_system;
  @(negedge clk);reset_n=0;uart_rx=1;bytes=0;repeat(5)@(posedge clk);@(negedge clk);reset_n=1;repeat(8)@(posedge clk);
 endtask
 initial forever begin
  logic [7:0] value;@(negedge uart_tx);#160;must(!uart_tx,"TX start");#320;
  for(integer k=0;k<8;k++)begin value[k]=uart_tx;#320;end
  must(uart_tx,"TX stop");must(bytes<6,"no extra UART output");
  if(bytes<4)must(value==text.getc(bytes),"TX text");else must(value==(bytes==4?13:10),"CR LF");bytes++;
 end
 initial begin
  $readmemh("../programs/stream_demo.mem",image);reset_system();
  header(0);repeat(10)@(posedge clk);must(boot_error && !running,"reject zero size");
  header(4097);repeat(10)@(posedge clk);must(boot_error && !running,"reject oversized image");
  frame(2,1);must(boot_error && !running && !dut.u_soc.imem_req_valid,"CRC failure holds CPU reset");
  header(4);send_byte(8'h12);repeat(2100)@(posedge clk);must(boot_error && !running,"truncated frame timeout");
  reset_system();send_byte(8'h46,1);repeat(12)@(posedge clk);must(boot_error && !running,"framing error");
  reset_system();header(2239);
  for(integer k=0;k<16;k++)send_byte(k);
  reset_system();must(!running && debug_status==0,"reset cancels partial load");
  begin
   logic [31:0] saved;saved=image[0];image[0]=32'h00100073;
   frame(1,0);must(!running,"CPU held during instruction-tail zero fill");wait(running);wait(debug_status[2]);#1;
   must(debug_status==32'h1204 && fault_pc==0,"one-word program executes after fill");
   must(dut.u_soc.u_imem.banks[0].u_sram.mem[1]===0 && dut.u_soc.u_imem.banks[7].u_sram.mem[511]===0,"unloaded instruction tail deterministically zero");
   image[0]=saved;reset_system();
  end
  for(integer run=0;run<2;run++)begin
   if(run)reset_system();
   frame(2239,0);wait(running);must(running && !boot_error,"validated image releases CPU");
   wait(debug_status[2]);#1;must(debug_status==32'h1205 && gpio_out==5 && bytes==6,"real UART load executes complete C self-check ROM");
   $display("PASS ASIC BOOT run=%0d image_words=2239 checks=137 UART=6",run);
  end
  reset_system();
  for(integer k=0;k<4096;k++)image[k]=32'h00000013;
  image[0]=32'h00100073;image[4095]=32'h5aa5c33c;
  frame(4096,0);must(running && !boot_error,"maximum image needs no tail fill");
  wait(debug_status[2]);#1;
  must(debug_status==32'h1204 && fault_pc==0,"maximum image executes");
  must(dut.u_soc.u_imem.banks[0].u_sram.mem[1]===32'h00000013 &&
       dut.u_soc.u_imem.banks[7].u_sram.mem[511]===32'h5aa5c33c,"maximum image preserves all loaded words");
  $display("PASS ASIC BOOT maximum image_words=4096, no tail fill");
  $display("ALL ASIC UART BOOT TESTS PASSED; 2 FULL PROGRAM RUNS, SHORT-IMAGE ZERO FILL AND MAXIMUM IMAGE; INVALID SIZE, CRC, TIMEOUT, FRAME ERROR AND RESET");$finish;
 end
 initial begin #150000000;$fatal(1,"ASIC boot timeout");end
endmodule
