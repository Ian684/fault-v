`timescale 1ns/1ps
module tb_loader_priority;
 logic clk=0;always #5 clk=~clk;
 logic rst=1,rx=1;
 wire running,boot_error,boot_valid;
 wire [31:0] boot_addr,boot_wdata;wire [3:0] boot_wstrb;
 logic boot_ready=1;
 integer writes=0;
 logic [7:0] packet[0:13];
 fault_v_loader #(.CLKS_PER_BIT(8),.TIMEOUT_CLKS(2000)) dut(.*);
 always @(posedge clk)if(!rst && boot_valid && boot_ready)writes++;
 task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"PRIORITY %s running=%b error=%b",msg,running,boot_error);endtask
 task automatic send_byte(input logic [7:0] value);
  @(negedge clk);rx=0;repeat(8)@(negedge clk);
  for(integer k=0;k<8;k++)begin rx=value[k];repeat(8)@(negedge clk);end
  rx=1;repeat(10)@(negedge clk);
 endtask
 initial begin
  $readmemh("../programs/short_packet.hex",packet);
  repeat(5)@(posedge clk);@(negedge clk);rst=0;
  for(integer k=0;k<14;k++)send_byte(packet[k]);
  wait(boot_valid && boot_addr==32'd16380);
  @(negedge clk);force dut.frame_error=1'b1;
  @(posedge clk);#1;
  must(!running && boot_error,"framing error overrides final fill start");
  @(negedge clk);release dut.frame_error;
  repeat(8)@(posedge clk);#1;must(!running && !boot_valid,"aborted image stays stopped");
  for(integer k=0;k<14;k++)send_byte(packet[k]);
  wait(running);#1;
  must(!boot_error && writes==8192,"retry reloads and fills the complete instruction image");
  $display("ALL LOADER ERROR PRIORITY CHECKS PASSED; FINAL FILL COLLISION AND RETRY");$finish;
 end
 initial begin #1000000;$fatal(1,"loader priority timeout");end
endmodule
