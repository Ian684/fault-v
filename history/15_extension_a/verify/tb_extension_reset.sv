`timescale 1ns/1ps
module tb_custom_reset;
 import fault_v_pkg::*;
 logic clk=0,rst=1;always #5 clk=~clk;
 wire halted,retire_valid;wire [31:0] pc;
 halt_cause_t halt_cause;cpu_state_t state;
 fault_v_soc dut(.clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(),.uart_tx(),
 .halted(halted),.halt_cause(halt_cause),.program_status(),.pc(pc),.state(state),
 .fault_pc(),.fault_addr(),.retire_valid(retire_valid),.retire_rd_we(),.retire_pc(),
 .retire_instruction(),.retire_rd_data(),.retire_rd_addr());
 integer commits=0,passed=0,op,stage;logic [31:0] want;
 always @(posedge clk)if(rst)commits=0;else if(retire_valid && dut.u_cpu.ir[6:0]==7'h0b)commits++;
 function automatic logic [31:0] golden(input integer n);
  case(n)
   0:golden=32'h00000046;
   1:golden=32'h000c1005;
   2:golden=32'h0c0a0806;
   3:golden=32'h0000007f;
   4:golden=32'h0000004f;
   5:golden=32'h000c100e;
   6:golden=32'h0c0a0806;
   7:golden=32'hfcfcfcfc;
   8:golden=32'h0000007f;
   9:golden=32'h002c441a;
   10:golden=32'h00000006;
   11:golden=32'h00000046;
   default:golden=0;
  endcase
 endfunction
 task automatic must(input logic ok,input string msg);
  if(ok!==1'b1)$fatal(1,"FAIL reset op=%0d stage=%0d: %s",op,stage,msg);
 endtask
 task automatic prepare;
  @(negedge clk);rst=1;@(posedge clk);#1;
  dut.u_imem.mem[0]=32'h040300b7;dut.u_imem.mem[1]=32'h20108093;
  dut.u_imem.mem[2]=32'h08070137;dut.u_imem.mem[3]=32'h60510113;
  dut.u_imem.mem[4]=32'h00900293;
  dut.u_imem.mem[5]=(op<4)?((op<<12)|32'h0020828b):(((op-4)<<12)|32'h0220828b);
  dut.u_imem.mem[6]=32'h00100073;
  @(negedge clk);rst=0;
 endtask
 initial begin
  for(op=0;op<12;op++)for(stage=0;stage<6;stage++)begin
   if(stage==1 && !(op==4 || op==5))continue;
   if(stage==3 && !(op==8 || op==10))continue;
   prepare();
   case(stage)
    0:wait(state==ST_CUSTOM_START);
    1:wait(state==ST_CUSTOM_ACC_READ);
    2:wait(state==ST_CUSTOM_WAIT && dut.u_cpu.u_custom.state==1);
    3:wait(dut.u_cpu.u_custom.state==2 || dut.u_cpu.u_custom.state==3);
    4:wait(dut.u_cpu.custom_rsp_valid);
    5:wait(state==ST_CUSTOM_COMMIT);
   endcase
   @(negedge clk);rst=1;#1;
   must(!retire_valid && !dut.u_cpu.custom_req_valid && !dut.u_cpu.custom_rsp_ready,"reset gates side effects");
   @(posedge clk);#1;
   must(pc==0 && dut.u_cpu.custom_acc==0 && dut.u_cpu.custom_result==0 && !dut.u_cpu.custom_rsp_valid,"clears saved accumulator and response");
   prepare();wait(halted);#1;want=golden(op);
   must(halt_cause==HALT_EBREAK && commits==1 && dut.u_cpu.u_regfile.regs[5]===want,"one exact result after restart");
   passed++;
  end
  must(passed==52,"all reset positions");
  $display("ALL 52 CUSTOM CPU RESET STAGES PASSED");$finish;
 end
 initial begin #300000;$fatal(1,"Reset timeout");end
endmodule
