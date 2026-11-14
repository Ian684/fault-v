`timescale 1ns/1ps
module tb_benchmark;
    import fault_v_pkg::*;
    logic clk=0;always #10 clk=~clk;
    logic [1:0] done=0;
    for(genvar g=0;g<2;g++)begin: modes
        logic rst=1;
        wire halted,uart_tx,retire_valid;
        wire [3:0] gpio_out;
        wire [31:0] program_status,pc,retire_pc,retire_instruction;
        halt_cause_t halt_cause;
        fault_v_soc #(.IMEM_DELAY(g==0?1:4),.DMEM_DELAY(g==0?1:7)) dut(
            .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),
            .halted(halted),.halt_cause(halt_cause),.program_status(program_status),.pc(pc),.state(),
            .fault_pc(),.fault_addr(),.retire_valid(retire_valid),.retire_rd_we(),.retire_pc(retire_pc),
            .retire_instruction(retire_instruction),.retire_rd_data(),.retire_rd_addr());
        logic measuring=0,started=0,ended=0;
        integer cycles=0,instructions=0,customs=0,fetches=0,loads=0,stores=0;
        integer global_cycles=0,id=0,repetition=0;
        logic [31:0] end_pc,halt_pc;
        logic [31:0] input_words[0:4095];
        logic [31:0] gold[0:63];
        integer indices[0:63];
        integer fd,total,scanned,expected_custom,out_count,index;
        string image;
        integer first_cycles[0:11],first_instructions[0:11];
        task automatic must(input logic ok,input string msg);
            if(ok!==1'b1)$fatal(1,"FAIL benchmark mode=%0d id=%0d repeat=%0d: %s pc=%h",g,id,repetition,msg,pc);
        endtask
        always @(posedge clk)begin
            if(rst)begin
                measuring=0;started=0;ended=0;cycles=0;instructions=0;customs=0;
                fetches=0;loads=0;stores=0;global_cycles=0;
            end else begin
                global_cycles++;
                must(global_cycles<1000000,"execution timeout");
                if(dut.imem_req_valid && dut.imem_req_ready)begin
                    if(dut.imem_req_addr==0)begin must(!started,"only one begin");started=1;measuring=1;end
                    if(dut.imem_req_addr==end_pc)begin must(started && !ended,"valid end marker");measuring=0;ended=1;end
                end
                if(measuring)begin
                    cycles++;
                    if(dut.imem_req_valid && dut.imem_req_ready)fetches++;
                    if(dut.dmem_req_valid && dut.dmem_req_ready)begin
                        must(dut.dmem_req_addr>=32'h10000000 && dut.dmem_req_addr<32'h10004000,"kernel accesses RAM only");
                        if(dut.dmem_req_write)stores++;else loads++;
                    end
                    if(retire_valid)begin
                        must(retire_pc<end_pc,"retire within kernel");instructions++;
                        if(retire_instruction[6:0]==7'h0b)customs++;
                        must(!(retire_instruction[6:0]==7'h33 && retire_instruction[31:25]==7'h01),"no standard M extension");
                    end
                end
            end
        end
        initial begin
            $readmemh("../programs/inputs.mem",input_words);
            fd=$fopen("../verify/benchmark.vec","r");must(fd!=0,"open benchmark vectors");
            scanned=$fscanf(fd,"%d",total);must(scanned==1 && total==12,"paired programs");
            for(integer c=0;c<total;c++)begin
                scanned=$fscanf(fd,"%d %s %h %h %d %d",id,image,end_pc,halt_pc,expected_custom,out_count);
                must(scanned==6 && out_count<=64,"program header");
                for(integer o=0;o<out_count;o++)begin
                    scanned=$fscanf(fd,"%d %h",indices[o],gold[o]);must(scanned==2,"output reference");
                end
                for(repetition=0;repetition<2;repetition++)begin
                    @(negedge clk);rst=1;repeat(3)@(posedge clk);#1;
                    for(integer m=0;m<4096;m++)begin dut.u_imem.mem[m]=0;dut.u_dmem.mem[m]=input_words[m];end
                    $readmemh(image,dut.u_imem.mem);
                    @(negedge clk);rst=0;wait(halted);#1;
                    must(halt_cause==HALT_EBREAK && pc==halt_pc && program_status==1,"successful termination");
                    must(started && ended && cycles>0 && instructions==fetches,"exact fetch/retire window");
                    must(customs==expected_custom,"custom count; baseline zero");
                    must(stores==out_count,"all output stores counted");
                    must(gpio_out==0 && uart_tx==1,"no serial/GPIO timing overhead");
                    for(integer o=0;o<out_count;o++)must(dut.u_dmem.mem[indices[o]]===gold[o],"every output matches golden");
                    if(repetition==0)begin first_cycles[id]=cycles;first_instructions[id]=instructions;end
                    else must(cycles==first_cycles[id] && instructions==first_instructions[id],"repeatable cycle and instruction counts");
                    $display("BENCH_RESULT mode=%0d id=%0d repeat=%0d cycles=%0d instructions=%0d custom=%0d loads=%0d stores=%0d outputs=%0d",g,id,repetition,cycles,instructions,customs,loads,stores,out_count);
                end
            end
            $fclose(fd);done[g]=1;
        end
    end
    initial begin wait(&done);$display("ALL 48 BENCHMARK RUNS PASSED; OUTPUTS AND REPEATED COUNTS VERIFIED");$finish;end
    initial begin #100000000;$fatal(1,"Benchmark global timeout");end
endmodule
