module tb_fault_v_cpu;
    timeunit 1ns;
    timeprecision 1ps;
    import fault_v_pkg::*;
    logic clk=0,rst;
    always #5 clk=~clk;
    logic imem_req_valid,imem_req_ready,imem_rsp_valid,imem_rsp_err,imem_rsp_ready;
    logic [31:0] imem_req_addr,imem_rsp_data;
    logic dmem_req_valid,dmem_req_ready,dmem_req_write,dmem_rsp_valid,dmem_rsp_err,dmem_rsp_ready;
    logic [31:0] dmem_req_addr,dmem_req_wdata,dmem_rsp_data;
    logic [3:0] dmem_req_wstrb;
    logic halted;
    halt_cause_t halt_cause;
    logic [31:0] fault_pc,fault_addr,pc;
    cpu_state_t state;
    logic retire_valid,retire_rd_we;
    logic [31:0] retire_pc,retire_instruction,retire_rd_data;
    logic [4:0] retire_rd_addr;
    fault_v_cpu dut(.*);
    logic [31:0] program_words[0:63],expected_value[0:63],expected_regs[0:31];
    logic [4:0] expected_rd[0:63];
    integer program_len,expected_commits,retired,requests,cycles,scenarios=0;
    integer mode,error_index,request_timer,response_timer,accepted_index,j;
    logic busy,stalled;
    logic [31:0] stalled_addr,previous_pc;
    logic previous_commit;

    task automatic must(input logic condition,input string label_text);
        if (condition !== 1'b1)
            $fatal(1,"FAIL %s state=%0d pc=%h retired=%0d",label_text,state,pc,retired);
    endtask
    task automatic tick; @(posedge clk); #1; endtask
    task automatic load_long_program;
        `include "program_init.svh"
    endtask
    task automatic reset_core;
        @(negedge clk); rst=1;
        tick; @(negedge clk); rst=0;
    endtask

    // Instruction memory stand-in: one accepted request, held response.
    always @(posedge clk) begin
        if (rst) begin
            imem_req_ready<=0; imem_rsp_valid<=0; imem_rsp_err<=0; imem_rsp_data<=0;
            busy<=0; request_timer<=0; response_timer<=0; accepted_index<=0; requests<=0;
        end else begin
            if (!busy) begin
                if (imem_req_valid && !imem_req_ready) begin
                    if (request_timer>=((mode==0)?0:(requests%4))) imem_req_ready<=1;
                    else request_timer<=request_timer+1;
                end
                if (imem_req_valid && imem_req_ready) begin
                    busy<=1; imem_req_ready<=0; requests<=requests+1;
                    accepted_index<=imem_req_addr[31:2];
                    response_timer<=(mode==0)?0:((requests+mode)%5);
                end
            end else if (!imem_rsp_valid) begin
                if (response_timer==0) begin
                    imem_rsp_valid<=1;
                    imem_rsp_err<=((accepted_index==error_index) || (accepted_index>=program_len));
                    if (accepted_index<program_len) imem_rsp_data<=program_words[accepted_index];
                    else imem_rsp_data<=0;
                end else response_timer<=response_timer-1;
            end
            if (imem_rsp_valid && imem_rsp_ready) begin
                imem_rsp_valid<=0; busy<=0; request_timer<=0;
            end
        end
    end

    // Commit trace is sampled before the same edge changes PC and RF.
    always @(posedge clk) begin
        if (rst) begin
            retired=0; stalled=0; previous_pc=0; previous_commit=0;
            for (integer r=0;r<32;r=r+1) expected_regs[r]=0;
        end else begin
            must(!dmem_req_valid && !dmem_rsp_ready,"unimplemented data path remains inactive");
            if (stalled) must(imem_req_valid && imem_req_addr==stalled_addr,"request stable during backpressure");
            if (!previous_commit) must(pc==previous_pc,"PC held until commit");
            if (retire_valid) begin
                must(retired<expected_commits,"no extra commits");
                must(retire_pc==retired*4,"sequential instruction PC");
                must(retire_instruction===program_words[retired],"executed requested instruction");
                must(retire_rd_we== (expected_rd[retired]!=0),"write enable including x0");
                must(retire_rd_addr===expected_rd[retired] && retire_rd_data===expected_value[retired],"destination and result");
                if (expected_rd[retired]!=0) expected_regs[expected_rd[retired]]=expected_value[retired];
                retired=retired+1;
            end
            stalled=imem_req_valid && !imem_req_ready; stalled_addr=imem_req_addr;
            previous_pc=pc; previous_commit=retire_valid;
        end
    end

    task automatic await_halt(input string label_text,input halt_cause_t cause,
                              input logic [31:0] expected_fault_pc,expected_fault_addr);
        cycles=0;
        while (!halted) begin
            tick; cycles=cycles+1;
            if (cycles>3000) $fatal(1,"TIMEOUT %s",label_text);
        end
        must(retired==expected_commits,"all expected instructions committed");
        must(halt_cause==cause && fault_pc==expected_fault_pc && fault_addr==expected_fault_addr,"termination cause/context");
        must(pc==expected_fault_pc,"stopped PC");
        must(requests==expected_commits+1,"one fetch per instruction including stop");
        for (integer r=0;r<32;r=r+1)
            must(dut.u_regfile.regs[r]===expected_regs[r],"final register file matches golden trace");
        repeat(4) tick;
        must(!imem_req_valid && !retire_valid && retired==expected_commits,"halt remains inactive");
        scenarios=scenarios+1;
        $display("PASS %0d: %s committed=%0d requests=%0d pc=%h cause=%0d",scenarios,label_text,retired,requests,pc,halt_cause);
    endtask

    task automatic short_fault(input string label_text,input logic [31:0] second,
                               input halt_cause_t cause,input logic fetch_error);
        @(negedge clk); rst=1;
        program_words[0]=32'h00500093; expected_rd[0]=1; expected_value[0]=5;
        program_words[1]=second; program_len=2; expected_commits=1;
        mode=2; error_index=fetch_error?1:-1;
        tick; @(negedge clk); rst=0;
        await_halt(label_text,cause,4,fetch_error?4:0);
    endtask

    initial begin
        rst=1; mode=0; error_index=-1;
        dmem_req_ready=0; dmem_rsp_valid=0; dmem_rsp_err=0; dmem_rsp_data=0;
        for (j=0;j<64;j=j+1) begin program_words[j]=0; expected_rd[j]=0; expected_value[j]=0; end
        for (j=0;j<3;j=j+1) begin
            @(negedge clk); rst=1; mode=j; error_index=-1; load_long_program;
            tick; @(negedge clk); rst=0;
            await_halt("dependent integer program",HALT_EBREAK,expected_commits*4,0);
        end
        short_fault("load not yet supported",32'h00002083,HALT_ILLEGAL,0);
        short_fault("branch not yet supported",32'h00000063,HALT_ILLEGAL,0);
        short_fault("jump not yet supported",32'h0000006f,HALT_ILLEGAL,0);
        short_fault("MUL not supported",32'h027302b3,HALT_ILLEGAL,0);
        short_fault("illegal shift encoding",32'h02009093,HALT_ILLEGAL,0);
        short_fault("ECALL stops with own cause",32'h00000073,HALT_ECALL,0);
        short_fault("fetch failure preserves prior write",32'h00100073,HALT_FETCH_ACCESS,1);

        @(negedge clk); rst=1; mode=2; error_index=-1; load_long_program;
        tick; @(negedge clk); rst=0;
        while (!busy) tick;
        // Both the core and memory model share reset, so the old response is cancelled.
        reset_core;
        await_halt("reset during accepted fetch then restart",HALT_EBREAK,expected_commits*4,0);
        $display("ALL %0d INTEGER CPU PROGRAM SCENARIOS PASSED",scenarios);
        $finish;
    end
    initial begin #1000000; $fatal(1,"GLOBAL TIMEOUT tb_fault_v_cpu"); end
endmodule
