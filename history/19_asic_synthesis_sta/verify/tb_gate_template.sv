`timescale 1ns/1ps
module tb_gate;
 logic clk=0;always #20 clk=~clk;
 logic reset_n=0,uart_rx=1;
 logic [1:0] gpio_in=0;
 wire uart_tx,running,boot_error;wire [3:0] gpio_out;wire [31:0] debug_status,fault_pc,fault_addr;
 fault_v_asic_top dut(.*);
 logic [7:0] packet[0:@PACKET_BYTES@-1];
 task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"GATE %s status=%h pc=%h addr=%h",msg,debug_status,fault_pc,fault_addr);endtask
 task automatic send_byte(input logic [7:0] value);
  @(negedge clk);uart_rx=0;repeat(217)@(negedge clk);
  for(integer k=0;k<8;k++)begin uart_rx=value[k];repeat(217)@(negedge clk);end
  uart_rx=1;repeat(217)@(negedge clk);repeat(2)@(negedge clk);
 endtask
 initial begin
  $readmemh("../programs/gate_packet.hex",packet);
  repeat(5)@(posedge clk);@(negedge clk);reset_n=1;repeat(10)@(posedge clk);
  must(!running,"held before load");
  for(integer k=0;k<@PACKET_BYTES@;k++)begin
   send_byte(packet[k]);
   if(k%256==0)$display("GATE UART bytes=%0d/@PACKET_BYTES@",k);
  end
  wait(running);must(running && !boot_error,"actual UART packet accepted");
  wait(debug_status[2]);#1;
  must(debug_status==32'h1205 && gpio_out==5 && fault_pc==@HALT_PC@,"all twelve custom op results, DMA and independent DOT4 checks");
  $display("ALL MAPPED GATE PROGRAM CHECKS PASSED; REAL UART BOOT; 12 CUSTOM OPS, DMA AND ACCELERATOR");$finish;
 end
 initial begin #300000000;$fatal(1,"gate timeout");end
endmodule
