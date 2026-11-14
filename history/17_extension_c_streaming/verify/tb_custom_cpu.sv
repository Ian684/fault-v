`timescale 1ns/1ps
module tb_custom_cpu;
    import fault_v_pkg::*;
    logic clk=0;always #5 clk=~clk;
    logic [1:0] done=0;
    for(genvar g=0;g<2;g++)begin: modes
        logic rst=1;
        wire halted,uart_tx,retire_valid,retire_rd_we;
        wire [3:0] gpio_out;
        wire [31:0] program_status,pc,fault_pc,fault_addr,retire_pc,retire_instruction,retire_rd_data;
        wire [4:0] retire_rd_addr;
        halt_cause_t halt_cause;cpu_state_t state;
        fault_v_soc #(.IMEM_DELAY(g==0?1:4),.DMEM_DELAY(g==0?1:7)) dut(
            .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),
            .halted(halted),.halt_cause(halt_cause),.program_status(program_status),
            .pc(pc),.fault_pc(fault_pc),.fault_addr(fault_addr),.state(state),
            .retire_valid(retire_valid),.retire_rd_we(retire_rd_we),.retire_pc(retire_pc),
            .retire_instruction(retire_instruction),.retire_rd_data(retire_rd_data),.retire_rd_addr(retire_rd_addr));
        integer retired,requests,responses,custom_starts,custom_responses;
        integer fd,total,words,traces,cause,customs,scanned,temp_rd,cycles,id=0;
        logic [31:0] stop_pc,want_ram,temp_word;
        logic [31:0] gold_pc[0:63],gold_inst[0:63],gold_data[0:63],gold_regs[0:31];
        logic [4:0] gold_rd[0:63];
        logic [31:0] previous_pc;
        logic previous_commit;
        task automatic must(input logic ok,input string msg);
            if(ok!==1'b1)$fatal(1,"FAIL custom CPU mode=%0d case=%0d: %s pc=%h",g,id,msg,pc);
        endtask
        always @(posedge clk)begin
            if(rst)begin
                retired=0;requests=0;responses=0;custom_starts=0;custom_responses=0;
                previous_pc=0;previous_commit=0;
            end else begin
                must(pc===previous_pc+(previous_commit?32'd4:32'd0),"PC only changes at commit");
                if(state inside {ST_CUSTOM_ACC_READ,ST_CUSTOM_START,ST_CUSTOM_WAIT,ST_CUSTOM_COMMIT})begin
                    must(!dut.imem_req_valid && !dut.dmem_req_valid,"no memory request during custom instruction");
                    if(state!=ST_CUSTOM_COMMIT)must(!retire_valid && !dut.u_cpu.reg_we,"no early writeback");
                end
                if(dut.u_cpu.custom_req_valid && dut.u_cpu.custom_req_ready)custom_starts++;
                if(dut.u_cpu.custom_rsp_valid && dut.u_cpu.custom_rsp_ready)custom_responses++;
                if(dut.dmem_req_valid && dut.dmem_req_ready)requests++;
                if(dut.dmem_rsp_valid && dut.dmem_rsp_ready)responses++;
                if(retire_valid)begin
                    must(retired<traces,"no extra retire");
                    must(retire_pc===gold_pc[retired] && retire_instruction===gold_inst[retired],"retired PC and encoding");
                    must(retire_rd_we==(gold_rd[retired]!=0) && retire_rd_addr===gold_rd[retired] && retire_rd_data===gold_data[retired],"writeback reference");
                    retired++;
                end
                previous_pc=pc;previous_commit=retire_valid;
            end
        end
        initial begin
            fd=$fopen("../verify/cpu.vec","r");must(fd!=0,"open CPU vectors");
            scanned=$fscanf(fd,"%d",total);must(scanned==1,"CPU vector count");
            for(id=0;id<total;id++)begin
                @(negedge clk);rst=1;@(posedge clk);#1;
                for(integer m=0;m<4096;m++)begin dut.u_imem.mem[m]=0;dut.u_dmem.mem[m]=0;end
                scanned=$fscanf(fd,"%d %d %d %h %h %d",words,traces,cause,stop_pc,want_ram,customs);
                must(scanned==6 && words<=64 && traces<=64,"case header");
                for(integer m=0;m<words;m++)begin scanned=$fscanf(fd,"%h",temp_word);must(scanned==1,"instruction word");dut.u_imem.mem[m]=temp_word;end
                for(integer m=0;m<traces;m++)begin
                    scanned=$fscanf(fd,"%h %h %d %h",gold_pc[m],gold_inst[m],temp_rd,gold_data[m]);
                    must(scanned==4,"trace row");gold_rd[m]=temp_rd;
                end
                for(integer m=0;m<32;m++)begin scanned=$fscanf(fd,"%h",gold_regs[m]);must(scanned==1,"register row");end
                @(negedge clk);rst=0;cycles=0;
                while(!halted)begin @(posedge clk);#1;cycles++;must(cycles<2000,"bounded CPU completion");end
                must(retired==traces && custom_starts==customs && custom_responses==customs,"exact custom accept/response/retire counts");
                must(halt_cause==cause && pc===stop_pc && fault_pc===stop_pc && fault_addr==0,"halt context");
                must(dut.u_dmem.mem[0]===want_ram && requests==responses,"RAM and memory handshakes");
                for(integer m=0;m<32;m++)must(dut.u_cpu.u_regfile.regs[m]===gold_regs[m],"register state");
                repeat(3)begin @(posedge clk);#1;must(!retire_valid && !dut.u_cpu.custom_req_valid,"quiet after halt");end
            end
            $fclose(fd);$display("PASS CUSTOM CPU mode=%0d cases=%0d",g,total);done[g]=1;
        end
    end
    initial begin wait(&done);$display("ALL 3822 CUSTOM CPU CASE RUNS PASSED");$finish;end
    initial begin #10000000;$fatal(1,"Custom CPU timeout");end
endmodule
