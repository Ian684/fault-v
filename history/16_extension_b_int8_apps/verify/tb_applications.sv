`timescale 1ns/1ps
module tb_applications;
 import fault_v_pkg::*;
 logic clk=0;always #10 clk=~clk;
 logic [1:0] done=0;
 for(genvar g=0;g<2;g++)begin:modes
  logic rst=1;wire halted,uart_tx,retire_valid;
  wire [3:0] gpio_out;wire [31:0] program_status,pc,retire_pc,retire_instruction;
  halt_cause_t halt_cause;
  fault_v_soc #(.IMEM_DELAY(g==0?1:4),.DMEM_DELAY(g==0?1:7)) dut(
   .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),.halted(halted),.halt_cause(halt_cause),
   .program_status(program_status),.pc(pc),.state(),.fault_pc(),.fault_addr(),.retire_valid(retire_valid),
   .retire_rd_we(),.retire_pc(retire_pc),.retire_instruction(retire_instruction),.retire_rd_data(),.retire_rd_addr());
  logic measuring=0,started=0,ended=0;
  integer cycles=0,instructions=0,customs=0,fetches=0,loads=0,stores=0,extra=0,global_cycles=0;
  integer id=0,repetition=0,cancellations=0;
  logic [31:0] end_pc,halt_pc,input_words[0:4095],gold[0:63];
  integer indices[0:63],first_cycles[0:127],first_instructions[0:127];
  integer fd,total,scanned,out_count,e_inst,e_custom,e_load,e_store,e_extra;
  string image,input_image;
  task automatic must(input logic ok,input string msg);
   if(ok!==1'b1)$fatal(1,"FAIL application mode=%0d id=%0d repeat=%0d: %s pc=%h",g,id,repetition,msg,pc);
  endtask
  always @(posedge clk)begin
   if(rst)begin
    measuring=0;started=0;ended=0;cycles=0;instructions=0;customs=0;fetches=0;loads=0;stores=0;extra=0;global_cycles=0;
   end else if(!done[g])begin
    global_cycles++;must(global_cycles<1000000,"bounded completion");
    if(dut.imem_req_valid && dut.imem_req_ready)begin
     if(dut.imem_req_addr==0)begin must(!started,"single begin");started=1;measuring=1;end
     if(dut.imem_req_addr==end_pc)begin must(started && !ended,"end follows begin");measuring=0;ended=1;end
    end
    if(measuring)begin
     cycles++;
     if(dut.imem_req_valid && dut.imem_req_ready)fetches++;
     if(dut.dmem_req_valid && dut.dmem_req_ready)begin
      must(dut.dmem_req_addr>=32'h10000000 && dut.dmem_req_addr<32'h10004000,"RAM only in measured region");
      if(dut.dmem_req_write)stores++;else loads++;
     end
     if(retire_valid)begin
      must(retire_pc<end_pc,"commit within region");instructions++;
      if(retire_instruction[6:0]==7'h0b)begin
       customs++;extra+=2;
       if(retire_instruction[31:25]==1 && retire_instruction[14:12] inside {0,1,4,6})extra++;
      end
      must(!(retire_instruction[6:0]==7'h33 && retire_instruction[31:25]==1),"no M instruction");
     end
    end
   end
  end
  initial begin
   fd=$fopen("../verify/applications.vec","r");must(fd!=0,"open vectors");scanned=$fscanf(fd,"%d",total);must(scanned==1 && total==68,"68 images");
   for(integer c=0;c<total;c++)begin
    scanned=$fscanf(fd,"%d %s %s %h %h %d %d %d %d %d %d",id,image,input_image,end_pc,halt_pc,out_count,e_inst,e_custom,e_load,e_store,e_extra);
    must(scanned==11 && out_count<=64,"case header");
    for(integer o=0;o<out_count;o++)begin scanned=$fscanf(fd,"%d %h",indices[o],gold[o]);must(scanned==2,"gold row");end
    $readmemh(input_image,input_words);
    for(repetition=0;repetition<3;repetition++)begin
     @(negedge clk);rst=1;repeat(3)@(posedge clk);#1;
     if(repetition<2)begin
      for(integer m=0;m<4096;m++)begin dut.u_imem.mem[m]=0;dut.u_dmem.mem[m]=input_words[m];end
      $readmemh(image,dut.u_imem.mem);
     end
     @(negedge clk);rst=0;
     if(repetition==2)begin
      // Run into a pending RAM transaction, reset, then restart with retained RAM.
      while(!dut.bus_pending || instructions<20)@(negedge clk);
      rst=1;#1;must(!retire_valid && !dut.dmem_req_valid && !dut.imem_req_valid,"reset gates requests and commit");
      repeat(3)@(posedge clk);@(negedge clk);rst=0;cancellations++;
     end
     wait(halted);#1;
     must(halt_cause==HALT_EBREAK && program_status==1 && pc==halt_pc,"success termination");
     must(started && ended && fetches==instructions,"exact measurement window");
     must(instructions==e_inst && customs==e_custom && loads==e_load && stores==e_store && extra==e_extra,"binary reference instruction and transaction counts");
     must(cycles==((g==0?1:4)+5)*instructions+((g==0?1:7)+3)*loads+((g==0?1:7)+2)*stores+extra,"independent cycle formula");
     must(uart_tx==1 && gpio_out==0,"no IO overhead");
     for(integer o=0;o<out_count;o++)must(dut.u_dmem.mem[indices[o]]===gold[o],"all raw/packed/state outputs");
     for(integer m=0;m<448;m++)must(dut.u_dmem.mem[m]===input_words[m],"input tensors/coefficients preserved");
     if(repetition==0)begin first_cycles[id]=cycles;first_instructions[id]=instructions;end
     else must(cycles==first_cycles[id] && instructions==first_instructions[id],"fresh and retained-RAM restart reproduce counts");
     $display("APP_RESULT mode=%0d id=%0d repeat=%0d cycles=%0d instructions=%0d custom=%0d loads=%0d stores=%0d outputs=%0d extra=%0d",g,id,repetition,cycles,instructions,customs,loads,stores,out_count,extra);
    end
   end
   $fclose(fd);must(cancellations==68,"all interruption cases");done[g]=1;
  end
 end
 initial begin wait(&done);$display("ALL 408 APPLICATION RUNS PASSED; 136 MID-EXECUTION RESETS; BINARY COUNTS AND ALL OUTPUTS VERIFIED");$finish;end
 initial begin #1000000000;$fatal(1,"Application timeout");end
endmodule
