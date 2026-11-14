`timescale 1ns/1ps
module tb_custom_program;
    import fault_v_pkg::*;
    logic clk=0;always #5 clk=~clk;
    logic [1:0] done=0;
    for(genvar g=0;g<2;g++)begin: modes
        logic rst=1;
        wire halted,uart_tx;
        wire [3:0] gpio_out;
        wire [31:0] program_status,pc;
        halt_cause_t halt_cause;
        integer bytes=0,customs=0;
        string message="DSP OK";
        fault_v_soc #(.IMEM_FILE("../programs/custom_demo.mem"),.IMEM_DELAY(g==0?1:4),.DMEM_DELAY(g==0?1:7),.UART_CLKS_PER_BIT(8)) dut(
            .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),
            .halted(halted),.halt_cause(halt_cause),.program_status(program_status),.pc(pc),.state(),
            .fault_pc(),.fault_addr(),.retire_valid(),.retire_rd_we(),.retire_pc(),
            .retire_instruction(),.retire_rd_data(),.retire_rd_addr());
        task automatic must(input logic ok,input string msg);
            if(ok!==1'b1)$fatal(1,"FAIL custom program mode=%0d: %s",g,msg);
        endtask
        always @(posedge clk)if(rst)begin bytes=0;customs=0;end
            else if(dut.u_cpu.retire_valid && dut.u_cpu.ir[6:0]==7'h0b)customs++;
        initial forever begin
            logic [7:0] value;
            @(negedge uart_tx);#40;must(!uart_tx,"UART start");#80;
            for(integer k=0;k<8;k++)begin value[k]=uart_tx;#80;end
            must(uart_tx,"UART stop");
            must(bytes<8,"no extra UART bytes");
            if(bytes<6)must(value==message.getc(bytes),"UART text");
            else must(value==(bytes==6?8'h0d:8'h0a),"CR/LF");
            bytes++;
        end
        integer fd,count,index,scanned;
        logic [31:0] want;
        initial begin
            for(integer run=0;run<2;run++)begin
                @(negedge clk);rst=1;repeat(3)@(posedge clk);@(negedge clk);rst=0;
                wait(halted);#1;
                must(halt_cause==HALT_EBREAK && program_status==1 && gpio_out==5 && bytes==8 && customs==302,"complete self-check program");
                fd=$fopen("../verify/demo_outputs.vec","r");must(fd!=0,"open expected outputs");
                scanned=$fscanf(fd,"%d",count);must(scanned==1 && count==159,"output count");
                repeat(count)begin
                    scanned=$fscanf(fd,"%d %h",index,want);must(scanned==2,"output row");
                    must(dut.u_dmem.mem[index]===want,"full output array comparison");
                end
                $fclose(fd);
                $display("PASS CUSTOM PROGRAM mode=%0d run=%0d outputs=%0d customs=%0d UART=%0d",g,run,count,customs,bytes);
            end
            // Corrupt a first and a late result to exercise distant error jumps.
            for(integer late=0;late<2;late++)begin
                @(negedge clk);rst=1;repeat(3)@(posedge clk);@(negedge clk);rst=0;
                if(late)wait(customs==256);
                wait(dut.u_cpu.custom_rsp_valid);
                @(negedge clk);force dut.u_cpu.custom_rsp_result=32'hdeadbeef;
                @(posedge clk);@(negedge clk);release dut.u_cpu.custom_rsp_result;
                wait(halted);#1;
                must(halt_cause==HALT_EBREAK && program_status==2 && gpio_out==15 && bytes==0,"failure path reports error");
                must(dut.u_dmem.mem[511]!==0,"failure check id recorded");
                $display("PASS CUSTOM PROGRAM fault mode=%0d late=%0d check=%0d",g,late,dut.u_dmem.mem[511]);
            end
            done[g]=1;
        end
    end
    initial begin wait(&done);$display("ALL 4 CUSTOM PROGRAM RUNS AND 4 FAULT INJECTIONS PASSED");$finish;end
    initial begin #5000000;$fatal(1,"Custom program timeout");end
endmodule
