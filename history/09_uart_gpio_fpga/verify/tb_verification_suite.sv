module tb_verification_suite;
    timeunit 1ns; timeprecision 1ps;
    import fault_v_pkg::*;
    logic clk=0;
    always #5 clk=~clk;
    localparam string VECTOR_FILE="../verify/suite.vec";
    logic [1:0] done=0;
    for (genvar g=0;g<2;g=g+1) begin: modes
        logic rst=1,halted,retire_valid,retire_rd_we;
        logic [31:0] program_status,fault_pc,fault_addr,pc,retire_pc,retire_instruction,retire_rd_data;
        logic [4:0] retire_rd_addr;
        halt_cause_t halt_cause;
        cpu_state_t state;
        fault_v_soc #(.IMEM_DELAY((g==0)?1:4),.DMEM_DELAY((g==0)?1:7)) dut(.gpio_in(2'b0),.uart_tx(),.gpio_out(),.*);
        logic [31:0] gold_pc[0:4095],gold_inst[0:4095],gold_data[0:4095],gold_next[0:4095];
        logic [4:0] gold_rd[0:4095];
        logic [31:0] gold_regs[0:31],gold_ram[0:4095];
        logic [31:0] tx_addr[0:511],tx_data[0:511],tx_raw[0:511],tx_repeat_raw[0:511];
        logic [3:0] tx_mask[0:511];
        logic tx_write[0:511],tx_error[0:511];
        integer fd,total_cases,id,kind,focus_id,word_count,trace_count,tx_count,sparse_count,cause;
        logic [31:0] focus_pc,stop_pc,stop_addr,status_expected;
        integer retired,requests,responses,fetches,focus_hits,cycles,passed=0;
        integer scanned,temp_rd,temp_index,temp_write,temp_error;
        logic [31:0] temp_word,previous_pc,previous_next;
        logic previous_commit;
        logic [39:0] covered=0;
        task automatic must(input logic condition,input string label_text);
            if (condition!==1'b1) $fatal(1,"FAIL mode=%0d case=%0d %s pc=%h retired=%0d",g,id,label_text,pc,retired);
        endtask
        task automatic read_case;
            scanned=$fscanf(fd,"%d %d %d %h %d %d %d %d %d %h %h %h",id,kind,focus_id,focus_pc,word_count,trace_count,tx_count,sparse_count,cause,stop_pc,stop_addr,status_expected);
            must(scanned==12,"valid case header");
            must(word_count<=4096 && trace_count<=4096 && tx_count<=512,"vector bounds");
            for (integer m=0;m<4096;m=m+1) begin
                dut.u_imem.mem[m]=0; dut.u_dmem.mem[m]=0; gold_ram[m]=0;
            end
            for (integer m=0;m<word_count;m=m+1) begin
                scanned=$fscanf(fd,"%h",temp_word); must(scanned==1,"program word"); dut.u_imem.mem[m]=temp_word;
            end
            for (integer m=0;m<trace_count;m=m+1) begin
                scanned=$fscanf(fd,"%h %h %d %h %h",gold_pc[m],gold_inst[m],temp_rd,gold_data[m],gold_next[m]);
                must(scanned==5,"trace row");gold_rd[m]=temp_rd;
            end
            for (integer r=0;r<32;r=r+1) begin scanned=$fscanf(fd,"%h",gold_regs[r]); must(scanned==1,"register row"); end
            for (integer m=0;m<sparse_count;m=m+1) begin
                scanned=$fscanf(fd,"%d %h",temp_index,temp_word); must(scanned==2 && temp_index>=0 && temp_index<4096,"RAM row");
                gold_ram[temp_index]=temp_word;
            end
            for (integer m=0;m<tx_count;m=m+1) begin
                scanned=$fscanf(fd,"%h %d %h %h %h %d %h",tx_addr[m],temp_write,tx_data[m],tx_mask[m],tx_raw[m],temp_error,tx_repeat_raw[m]);
                must(scanned==7,"transaction row");tx_write[m]=temp_write;tx_error[m]=temp_error;
            end
        endtask
        always @(posedge clk) begin
            if (rst) begin
                retired=0;requests=0;responses=0;fetches=0;focus_hits=0;previous_pc=0;previous_commit=0;
            end else begin
                if (previous_commit) must(pc===previous_next,"next PC");
                else must(pc===previous_pc,"PC held until completion");
                if (dut.imem_req_valid && dut.imem_req_ready) fetches=fetches+1;
                if (dut.dmem_req_valid && dut.dmem_req_ready) begin
                    must(requests<tx_count,"no extra data request");
                    must(dut.dmem_req_addr===tx_addr[requests] && dut.dmem_req_write===tx_write[requests],"data address direction");
                    must(dut.dmem_req_wdata===tx_data[requests] && dut.dmem_req_wstrb===tx_mask[requests],"store payload and mask");
                    requests=requests+1;
                end
                if (dut.dmem_rsp_valid && dut.dmem_rsp_ready) begin
                    must(responses<tx_count,"no extra response");
                    must(dut.dmem_rsp_err===tx_error[responses] && dut.dmem_rsp_data===tx_raw[responses],"data response word and error");
                    responses=responses+1;
                end
                must(!((dut.u_imem.busy || dut.imem_rsp_valid) && (dut.u_dmem.busy || dut.dmem_rsp_valid)),"single outstanding transaction");
                if (retire_valid) begin
                    must(retired<trace_count,"no extra commit");
                    must(retire_pc===gold_pc[retired] && retire_instruction===gold_inst[retired],"instruction PC and word");
                    must(retire_rd_we==(gold_rd[retired]!=0),"rd enable including x0");
                    must(retire_rd_addr===gold_rd[retired] && retire_rd_data===gold_data[retired],"rd address and value");
                    if (focus_id>=0 && retire_pc==focus_pc) focus_hits=focus_hits+1;
                    previous_next=gold_next[retired];retired=retired+1;
                end
                previous_pc=pc;previous_commit=retire_valid;
            end
        end
        task automatic finish_check;
            must(retired==trace_count && fetches==trace_count+1,"commit and fetch count");
            must(requests==tx_count && responses==tx_count,"data count");
            must(halt_cause==cause && fault_pc===stop_pc && fault_addr===stop_addr && pc===stop_pc,"halt context");
            must(program_status===status_expected,"status including expected failure");
            for (integer r=0;r<32;r=r+1) must(dut.u_cpu.u_regfile.regs[r]===gold_regs[r],"all registers");
            for (integer m=0;m<4096;m=m+1) must(dut.u_dmem.mem[m]===gold_ram[m],"all data RAM words");
            if (focus_id>=0) begin
                must(focus_hits>0 || (fault_pc==focus_pc && cause!=1 && cause!=3),"target instruction actually exercised");
                covered[focus_id]=1;
            end
            repeat(3) begin @(posedge clk); #1; end
            must(!retire_valid && !dut.imem_req_valid && !dut.dmem_req_valid,"halt remains inactive");
            passed=passed+1;
        endtask
        initial begin
            fd=$fopen(VECTOR_FILE,"r"); must(fd!=0,"open suite vectors");
            scanned=$fscanf(fd,"%d",total_cases);must(scanned==1,"case count");
            for (integer c=0;c<total_cases;c=c+1) begin
                @(negedge clk);rst=1;
                @(posedge clk);#1;
                read_case;
                for (integer repeat_id=0;repeat_id<((kind==1)?2:1);repeat_id=repeat_id+1) begin
                    if (repeat_id>0) begin
                        @(negedge clk);rst=1;@(posedge clk);#1;
                        for (integer t=0;t<tx_count;t=t+1) tx_raw[t]=tx_repeat_raw[t];
                    end
                    must(pc==0 && program_status==0 && !halted,"clean core and status reset");
                    @(negedge clk);rst=0;cycles=0;
                    while (!halted) begin
                        @(posedge clk);#1;cycles=cycles+1;
                        if (cycles>100000) $fatal(1,"TIMEOUT mode=%0d case=%0d",g,id);
                    end
                    finish_check;
                    if (kind==1 || (id%50)==0) $display("PASS mode=%0d case=%0d repeat=%0d commits=%0d data=%0d status=%h",g,id,repeat_id,retired,requests,program_status);
                end
            end
            must(covered==40'hffffffffff,"40 of 40 instruction names observed");
            $display("COVERAGE mode=%0d names=40/40 bitmap=%h runs=%0d",g,covered,passed);
            $fclose(fd);done[g]=1;
        end
    end
    initial begin wait (&done);#1;$display("ALL 1372 ISA AND PROGRAM RUNS PASSED");$finish;end
    initial begin #20000000; $fatal(1,"GLOBAL TIMEOUT VERIFICATION SUITE");end
endmodule

