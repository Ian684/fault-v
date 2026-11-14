`timescale 1ns/1ps
module tb_gate_accept;
 logic clk=0;always #20 clk=~clk;
 logic reset_n=0,uart_rx=1;logic [1:0] gpio_in=0;
 wire uart_tx,running,boot_error;wire [3:0] gpio_out;wire [31:0] debug_status,fault_pc,fault_addr;
 fault_v_asic_top dut(.*);
 logic [7:0] packet[0:13];logic [31:0] image[0:205];
 task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"GATE %s status=%h pc=%h addr=%h",msg,debug_status,fault_pc,fault_addr);endtask
 task automatic send_byte(input logic [7:0] value);
  @(negedge clk);uart_rx=0;repeat(217)@(negedge clk);
  for(integer k=0;k<8;k++)begin uart_rx=value[k];repeat(217)@(negedge clk);end
  uart_rx=1;repeat(219)@(negedge clk);
 endtask
 task automatic reset_system;
  @(negedge clk);reset_n=0;uart_rx=1;repeat(5)@(posedge clk);
  @(negedge clk);reset_n=1;repeat(10)@(posedge clk);
 endtask
 task automatic preload(input integer index,input logic [31:0] value);
  case(index/512)
   0:dut.\u_soc.u_imem.banks[0].u_sram .mem[index%512]=value;
   1:dut.\u_soc.u_imem.banks[1].u_sram .mem[index%512]=value;
   2:dut.\u_soc.u_imem.banks[2].u_sram .mem[index%512]=value;
   3:dut.\u_soc.u_imem.banks[3].u_sram .mem[index%512]=value;
   4:dut.\u_soc.u_imem.banks[4].u_sram .mem[index%512]=value;
   5:dut.\u_soc.u_imem.banks[5].u_sram .mem[index%512]=value;
   6:dut.\u_soc.u_imem.banks[6].u_sram .mem[index%512]=value;
   7:dut.\u_soc.u_imem.banks[7].u_sram .mem[index%512]=value;
   default:$fatal(1,"bad simulated SRAM preload address");
  endcase
 endtask
 initial begin
  $readmemh("../programs/short_packet.hex",packet);
  $readmemh("../programs/gate_program.mem",image);
  reset_system();must(!running,"held before load");
  packet[10]=packet[10]^1;
  for(integer k=0;k<14;k++)send_byte(packet[k]);
  repeat(10)@(posedge clk);#1;
  must(boot_error && !running && debug_status==0,"mapped UART CRC error keeps CPU reset");
  $display("PASS MAPPED UART rejected bad CRC");$fflush();
  packet[10]=packet[10]^1;
  for(integer k=0;k<14;k++)send_byte(packet[k]);
  wait(running);wait(debug_status[2]);#1;
  must(!boot_error && debug_status==32'h1204 && fault_pc==0,"mapped UART boot and instruction-tail fill");
  must(dut.\u_soc.u_imem.banks[7].u_sram .mem[511]===0,"last instruction bank zero-filled");
  $display("PASS MAPPED UART valid one-word image, tail fill and EBREAK");$fflush();
  reset_system();
  // Simulated SRAM preload isolates CPU execution from serial transfer time.
  @(negedge clk);
  for(integer k=0;k<4096;k++)preload(k,0);
  for(integer k=0;k<206;k++)preload(k,image[k]);
  force dut.running=1'b1;
  wait(debug_status[2]);#1;
  must(debug_status==32'h1205 && gpio_out==5 && fault_pc==784,"12 custom ops, DMA and independent DOT4 result checks");
  release dut.running;
  $display("ALL MAPPED GATE PROGRAM CHECKS PASSED; REAL UART CRC/BOOT CASES; SRAM-PRELOADED 15-CHECK CPU CASE");$fflush();$finish;
 end
 initial begin #10000000;$fatal(1,"mapped gate acceptance timeout");end
endmodule
