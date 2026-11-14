`timescale 1ns/1ps
module tb_stream_demo;
 import fault_v_pkg::*;
 logic clk=0;always #5 clk=~clk;logic [1:0] done=0;
 for(genvar g=0;g<2;g++)begin:modes
  logic rst=1;wire halted,uart_tx;wire [31:0] program_status;wire [3:0] gpio_out;halt_cause_t halt_cause;
  integer bytes=0;string message="C OK";
  fault_v_soc #(.IMEM_FILE("../programs/stream_demo.mem"),.IMEM_DELAY(g==0?1:4),.DMEM_DELAY(g==0?1:7),.UART_CLKS_PER_BIT(8)) dut(
   .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),.program_status(program_status),.halted(halted),.halt_cause(halt_cause),
   .fault_pc(),.fault_addr(),.pc(),.state(),.retire_valid(),.retire_rd_we(),.retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
  task automatic must(input logic ok,input string msg);if(ok!==1)$fatal(1,"DEMO mode=%0d: %s",g,msg);endtask
  always @(posedge clk)if(rst)bytes=0;
  initial forever begin
   logic [7:0] value;@(negedge uart_tx);#40;must(!uart_tx,"start bit");#80;
   for(integer k=0;k<8;k++)begin value[k]=uart_tx;#80;end
   must(uart_tx,"stop bit");must(bytes<6,"no extra bytes");
   if(bytes<4)must(value==message.getc(bytes),"UART text");else must(value==(bytes==4?13:10),"CR LF");bytes++;
  end
  task automatic restart;
   @(negedge clk);rst=1;repeat(3)@(posedge clk);@(negedge clk);rst=0;
  endtask
  initial begin
   for(integer run=0;run<2;run++)begin
    restart();wait(halted);#1;must(halt_cause==HALT_EBREAK && program_status==1 && gpio_out==5 && bytes==6,"successful full demonstration");
    for(integer k=0;k<64;k++)begin must(dut.u_scratch.mem[k]===dut.u_dmem.mem[k],"DMA to scratch");must(dut.u_dmem.mem[2304+k]===dut.u_dmem.mem[2048+k],"disjoint DMA copy");end
    must(dut.u_dmem.mem[3072]===32'hfffef598 && dut.u_dmem.mem[3584]==100 && dut.u_scratch.mem[256]==32'h12348000,"independent dot, CPU and narrow access results");
    $display("PASS STREAM DEMO mode=%0d run=%0d checks=137 UART=6",g,run);
   end
   for(integer late=0;late<2;late++)begin
    restart();
    if(!late)begin
     wait(dut.u_acc.state==7);@(negedge clk);force dut.u_acc.accumulator=32'hdeadbeef;
     wait(dut.u_acc.state==8);@(negedge clk);release dut.u_acc.accumulator;
    end else begin
     wait(dut.dma_busy && dut.dma_a==32'h10002000);wait(!dut.dma_busy && dut.u_dma.done);
     @(negedge clk);dut.u_dmem.mem[2367]=dut.u_dmem.mem[2367]^1;
    end
    wait(halted);#1;$display("DEMO FAILURE DEBUG mode=%0d late=%0d cause=%0d status=%0d gpio=%h bytes=%0d check=%0d result=%h",g,late,halt_cause,program_status,gpio_out,bytes,dut.u_dmem.mem[511],dut.u_dmem.mem[3072]);must(halt_cause==HALT_EBREAK && program_status==2 && gpio_out==15 && bytes==0,"self-check failure reports error");
    must(dut.u_dmem.mem[511]==(late?134:65),"specific failed check ID");$display("PASS STREAM DEMO injected failure mode=%0d check=%0d",g,dut.u_dmem.mem[511]);
   end
   done[g]=1;
  end
 end
 initial begin wait(&done);$display("ALL 4 STREAM DEMO RUNS AND 4 INJECTED SELF-CHECK FAILURES PASSED");$finish;end
 initial begin #20000000;$fatal(1,"stream demo timeout");end
endmodule
