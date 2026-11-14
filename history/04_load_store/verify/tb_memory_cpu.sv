module tb_memory_cpu;
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
    logic [31:0] program_words[0:63],expected_value[0:255],expected_regs[0:31],golden_regs[0:31];
    logic [4:0] expected_rd[0:255];
    integer program_len,expected_commits,retired,requests,cycles,scenarios=0;
    integer mode,error_index,request_timer,response_timer,accepted_index,j;
    logic busy,stalled;
    logic [31:0] expected_pc[0:255],expected_inst[0:255],expected_next[0:255],previous_next;
    string case_name;
    halt_cause_t expected_cause;
    logic [31:0] expected_fault_pc,expected_fault_addr;
    integer case_id,delay_mode;
    logic [31:0] stalled_addr,previous_pc;
    logic previous_commit;

    logic [7:0] memory_bytes[0:259],golden_mem[0:259];
    logic [31:0] tx_addr[0:63],tx_data[0:63],tx_raw[0:63];
    logic tx_write[0:63],tx_error[0:63];
    logic [3:0] tx_mask[0:63];
    integer expected_transactions,transactions,responses,fail_write;
    logic [31:0] fail_addr;
    logic data_busy,data_stalled,captured_write;
    logic [31:0] captured_addr,captured_data,data_stalled_addr,data_stalled_value;
    logic [3:0] captured_mask,data_stalled_mask;
    logic data_stalled_write;
    integer data_request_timer,data_response_timer;
    function automatic logic mapped(input logic [31:0] addr);
        return (addr>=32'h10000000 && addr<32'h10000100) ||
               (addr>=32'h20000000 && addr<32'h20000004);
    endfunction
    function automatic integer mem_index(input logic [31:0] addr);
        if (addr>=32'h10000000 && addr<32'h10000100) return addr-32'h10000000;
        return 256+addr-32'h20000000;
    endfunction

    task automatic must(input logic condition,input string label_text);
        if (condition !== 1'b1)
            $fatal(1,"FAIL %s state=%0d pc=%h retired=%0d",label_text,state,pc,retired);
    endtask
    task automatic tick; @(posedge clk); #1; endtask
    task automatic load_case(input integer case_id);
        for (integer k=0;k<64;k=k+1) program_words[k]=0;
        `include "cases_init.svh"
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

    // Test endpoint: successful writes take effect only when the response handshakes.
    // Failed writes have no effect in this endpoint; this is not a universal bus guarantee.
    always @(posedge clk) begin
        if (rst) begin
            dmem_req_ready<=0; dmem_rsp_valid<=0; dmem_rsp_err<=0; dmem_rsp_data<=0;
            data_busy<=0; data_request_timer<=0; data_response_timer<=0;
            transactions<=0; responses<=0; captured_addr<=0; captured_write<=0;
            captured_data<=0; captured_mask<=0;
            for (integer m=0;m<260;m=m+1)
                memory_bytes[m]<=(m<256)?((m*73+128)&255):0;
        end else begin
            if (!data_busy) begin
                if (!dmem_rsp_valid) dmem_rsp_data<=32'hdeadbeef;
                if (dmem_req_valid && !dmem_req_ready) begin
                    if (data_request_timer>=((mode==0)?0:(transactions%4+1))) dmem_req_ready<=1;
                    else data_request_timer<=data_request_timer+1;
                end
                if (dmem_req_valid && dmem_req_ready) begin
                    must(transactions<expected_transactions,"no extra data transaction");
                    must(dmem_req_addr===tx_addr[transactions] && dmem_req_write===tx_write[transactions],"data address and direction");
                    must(dmem_req_wdata===tx_data[transactions] && dmem_req_wstrb===tx_mask[transactions],"store data and byte mask");
                    must(dmem_req_addr[1:0]==0,"external data address word aligned");
                    must(!busy && !imem_req_valid,"only one outstanding request across both channels");
                    transactions<=transactions+1; data_busy<=1; dmem_req_ready<=0;
                    captured_addr<=dmem_req_addr; captured_write<=dmem_req_write;
                    captured_data<=dmem_req_wdata; captured_mask<=dmem_req_wstrb;
                    data_response_timer<=(mode==0)?0:((transactions+mode)%6+1);
                end
            end else if (!dmem_rsp_valid) begin
                must(!dmem_req_valid,"accepted data transaction is not issued again");
                if (data_response_timer==0) begin
                    dmem_rsp_valid<=1;
                    if (!mapped(captured_addr) || (captured_addr==fail_addr && (fail_write<0 || captured_write==fail_write))) begin
                        dmem_rsp_err<=1; dmem_rsp_data<=0;
                    end else begin
                        dmem_rsp_err<=0;
                        dmem_rsp_data<={memory_bytes[mem_index(captured_addr)+3],memory_bytes[mem_index(captured_addr)+2],
                                        memory_bytes[mem_index(captured_addr)+1],memory_bytes[mem_index(captured_addr)]};
                    end
                end else data_response_timer<=data_response_timer-1;
            end
            if (dmem_rsp_valid && dmem_rsp_ready) begin
                must(dmem_rsp_err===tx_error[responses],"response error matches independent expected transaction");
                must(dmem_rsp_data===tx_raw[responses],"full raw response word matches byte-memory model");
                if (captured_write && !dmem_rsp_err)
                    for (integer lane=0;lane<4;lane=lane+1)
                        if (captured_mask[lane]) memory_bytes[mem_index(captured_addr)+lane]<=captured_data[lane*8 +: 8];
                responses<=responses+1; dmem_rsp_valid<=0; data_busy<=0; data_request_timer<=0;
            end
        end
    end

    // Commit trace is sampled before the same edge changes PC and RF.
    always @(posedge clk) begin
        if (rst) begin
            retired=0; stalled=0; previous_pc=0; previous_commit=0; data_stalled=0;
            for (integer r=0;r<32;r=r+1) expected_regs[r]=0;
        end else begin
            if (data_stalled) begin
                must(dmem_req_valid && dmem_req_addr===data_stalled_addr,"data request address stable under backpressure");
                must(dmem_req_write===data_stalled_write && dmem_req_wdata===data_stalled_value && dmem_req_wstrb===data_stalled_mask,"store payload stable under backpressure");
            end
            data_stalled=dmem_req_valid && !dmem_req_ready;
            data_stalled_addr=dmem_req_addr; data_stalled_write=dmem_req_write;
            data_stalled_value=dmem_req_wdata; data_stalled_mask=dmem_req_wstrb;
            if (stalled) must(imem_req_valid && imem_req_addr==stalled_addr,"request stable during backpressure");
            if (!previous_commit) must(pc==previous_pc,"PC held until commit");
            else must(pc===previous_next,"committed next PC");
            if (retire_valid) begin
                must(retired<expected_commits,"no extra commits");
                must(retire_pc===expected_pc[retired],"instruction PC");
                must(retire_instruction===expected_inst[retired],"executed requested instruction");
                must(retire_rd_we== (expected_rd[retired]!=0),"write enable including x0");
                must(retire_rd_addr===expected_rd[retired] && retire_rd_data===expected_value[retired],"destination and result");
                if (expected_rd[retired]!=0) expected_regs[expected_rd[retired]]=expected_value[retired];
                previous_next=expected_next[retired];
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
            begin
                must(dut.u_regfile.regs[r]===golden_regs[r],"final register file matches independent model");
                must(expected_regs[r]===golden_regs[r],"commit trace matches independent final state");
            end
        must(transactions==expected_transactions && responses==expected_transactions,"all data requests receive exactly one response");
        for (integer m=0;m<260;m=m+1)
            must(memory_bytes[m]===golden_mem[m],"all memory bytes match independent model");
        repeat(4) tick;
        must(!imem_req_valid && !dmem_req_valid && !dmem_rsp_ready && !retire_valid && retired==expected_commits,"halt remains inactive");
        scenarios=scenarios+1;
        $display("PASS %0d: %s committed=%0d requests=%0d pc=%h cause=%0d data=%0d",scenarios,label_text,retired,requests,pc,halt_cause,transactions);
    endtask

    initial begin
        rst=1; mode=0; error_index=-1;
        for (case_id=0;case_id<125;case_id=case_id+1) begin
            for (delay_mode=0;delay_mode<2;delay_mode=delay_mode+1) begin
                @(negedge clk); rst=1; mode=delay_mode*2; load_case(case_id);
                tick; @(negedge clk); rst=0;
                await_halt(case_name,expected_cause,expected_fault_pc,expected_fault_addr);
            end
        end
        // Cancel an accepted store or load while the test endpoint has not responded.
        for (integer k=0;k<2;k=k+1) begin
            @(negedge clk); rst=1; mode=2; load_case(87);
            tick; @(negedge clk); rst=0;
            cycles=0;
            while (!(data_busy && captured_write==(k==0))) begin
                tick; cycles=cycles+1;
                if (cycles>3000) $fatal(1,"reset setup timeout");
            end
            reset_core;
            await_halt("reset during pending data transaction then restart",expected_cause,expected_fault_pc,expected_fault_addr);
        end
        $display("ALL %0d MEMORY CPU SCENARIOS PASSED",scenarios);
        $finish;
    end
    initial begin #2000000; $fatal(1,"GLOBAL TIMEOUT tb_memory_cpu"); end
endmodule
