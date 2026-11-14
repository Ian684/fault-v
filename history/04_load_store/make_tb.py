from pathlib import Path
import json
root=Path(__file__).resolve().parent
cfg=json.loads((root/'case_config.json').read_text())
tb=(root/'reference_inputs/tb_branch_template.txt').read_text()
tb=tb[:tb.index('    initial begin\n        rst=1; mode=0;')]
tb=tb.replace('module tb_branch_cpu;','module tb_memory_cpu;')
pos=tb.index('    task automatic must')
decl='''    logic [7:0] memory_bytes[0:259],golden_mem[0:259];
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

'''
tb=tb[:pos]+decl+tb[pos:]
pos=tb.index('    // Commit trace')
model='''    // Test endpoint: successful writes take effect only when the response handshakes.
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

'''
tb=tb[:pos]+model+tb[pos:]
tb=tb.replace('previous_commit=0;','previous_commit=0; data_stalled=0;')
tb=tb.replace('            must(!dmem_req_valid && !dmem_rsp_ready,"unimplemented data path remains inactive");','''            if (data_stalled) begin
                must(dmem_req_valid && dmem_req_addr===data_stalled_addr,"data request address stable under backpressure");
                must(dmem_req_write===data_stalled_write && dmem_req_wdata===data_stalled_value && dmem_req_wstrb===data_stalled_mask,"store payload stable under backpressure");
            end
            data_stalled=dmem_req_valid && !dmem_req_ready;
            data_stalled_addr=dmem_req_addr; data_stalled_write=dmem_req_write;
            data_stalled_value=dmem_req_wdata; data_stalled_mask=dmem_req_wstrb;''')
tb=tb.replace('        repeat(4) tick;','''        must(transactions==expected_transactions && responses==expected_transactions,"all data requests receive exactly one response");
        for (integer m=0;m<260;m=m+1)
            must(memory_bytes[m]===golden_mem[m],"all memory bytes match independent model");
        repeat(4) tick;''')
tb=tb.replace('!imem_req_valid && !retire_valid && retired==expected_commits','!imem_req_valid && !dmem_req_valid && !dmem_rsp_ready && !retire_valid && retired==expected_commits')
tb=tb.replace('pc=%h cause=%0d",scenarios,label_text,retired,requests,pc,halt_cause','pc=%h cause=%0d data=%0d",scenarios,label_text,retired,requests,pc,halt_cause,transactions')
tb+='''    initial begin
        rst=1; mode=0; error_index=-1;
        for (case_id=0;case_id<CASE_COUNT;case_id=case_id+1) begin
            for (delay_mode=0;delay_mode<2;delay_mode=delay_mode+1) begin
                @(negedge clk); rst=1; mode=delay_mode*2; load_case(case_id);
                tick; @(negedge clk); rst=0;
                await_halt(case_name,expected_cause,expected_fault_pc,expected_fault_addr);
            end
        end
        // Cancel an accepted store or load while the test endpoint has not responded.
        for (integer k=0;k<2;k=k+1) begin
            @(negedge clk); rst=1; mode=2; load_case(LOOP_ID);
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
'''.replace('CASE_COUNT',str(cfg['programs'])).replace('LOOP_ID',str(cfg['loop_id']))
(root/'verify/tb_memory_cpu.sv').write_text(tb)
