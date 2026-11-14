module tb_control_fsm;
    timeunit 1ns;
    timeprecision 1ps;
    import fault_v_pkg::*;
    logic clk=0, rst;
    always #5 clk=~clk;
    instr_class_t instr_class;
    logic illegal,rd_write;
    mem_size_t mem_size;
    logic [31:0] pc,instr_pc,mem_addr,target_addr;
    logic branch_taken;
    logic imem_req_valid,imem_req_ready,imem_rsp_valid,imem_rsp_err,imem_rsp_ready;
    logic [31:0] imem_req_addr;
    logic dmem_req_valid,dmem_req_ready,dmem_req_write,dmem_rsp_valid,dmem_rsp_err,dmem_rsp_ready;
    logic [31:0] dmem_req_addr;
    logic ir_we,instr_pc_we,ab_we,aluout_we,branch_taken_we,mdr_we,reg_we,pc_we,instr_done;
    pc_sel_t pc_sel;
    cpu_state_t state;
    logic mem_pending,halted;
    halt_cause_t halt_cause;
    logic [31:0] fault_pc,fault_addr;
    control_fsm dut(.*);
    int checks=0,cases=0;
    integer rq,rs,k,s;
    cpu_state_t wanted;
    instr_class_t chosen;
    logic score_pending=0,score_data=0;
    logic stalled_i=0,stalled_d=0;
    logic [31:0] held_i_addr,held_d_addr;
    logic held_d_write;

    task automatic must(input logic cond,input string label_text);
        if (cond !== 1'b1)
            $fatal(1,"FAIL %s state=%0d pending=%b",label_text,state,mem_pending);
        checks++;
    endtask
    task automatic tick;
        @(posedge clk); #1;
    endtask
    task automatic reset_all;
        @(negedge clk);
        rst=1; instr_class=IC_ALU; illegal=0; rd_write=1; mem_size=MEM_WORD;
        pc=32'h100; instr_pc=32'h100; mem_addr=32'h10000004;
        target_addr=32'h200; branch_taken=0;
        imem_req_ready=0; imem_rsp_valid=0; imem_rsp_err=0;
        dmem_req_ready=0; dmem_rsp_valid=0; dmem_rsp_err=0;
        tick;
        must(state==ST_FETCH && !mem_pending && !halted,"reset state");
        must(halt_cause==HALT_NONE && fault_pc==0 && fault_addr==0,"reset debug");
        @(negedge clk); rst=0;
    endtask

    task automatic begin_instruction(input instr_class_t cl,
                                     input logic wr,input mem_size_t sz,
                                     input int req_delay,input int rsp_delay);
        reset_all;
        instr_class=cl; rd_write=wr; mem_size=sz;
        repeat(req_delay) begin
            #1;
            must(imem_req_valid && !imem_rsp_ready,"fetch request stall");
            tick;
            must(state==ST_FETCH && !mem_pending,"fetch not accepted");
            @(negedge clk);
        end
        // A response on the request-acceptance edge cannot be accepted yet.
        imem_req_ready=1; imem_rsp_valid=1;
        #1; must(!imem_rsp_ready && !ir_we,"no same-edge fetch response");
        tick;
        must(mem_pending && state==ST_FETCH,"fetch accepted once");
        @(negedge clk); imem_req_ready=0; imem_rsp_valid=0;
        repeat(rsp_delay) begin
            #1; must(!imem_req_valid && imem_rsp_ready && !ir_we,"fetch response wait");
            tick; @(negedge clk);
        end
        imem_rsp_valid=1;
        #1; must(ir_we && instr_pc_we && imem_rsp_ready,"successful fetch enables");
        tick;
        must(state==ST_DECODE && !mem_pending,"decode after fetch");
        @(negedge clk); imem_rsp_valid=0;
    endtask

    task automatic expect_stop(input halt_cause_t cause,
                               input logic [31:0] expected_pc,expected_addr);
        // Called before the edge on which the fault is sampled.
        #1;
        must(!pc_we && !reg_we && !instr_done && !dmem_req_valid && !imem_req_valid,
             "fault suppresses commit and requests");
        tick;
        must(halted && state==ST_HALTED,"enters halted");
        must(halt_cause==cause && fault_pc==expected_pc && fault_addr==expected_addr,
             "saved fault information");
        @(negedge clk);
        // Changes to external inputs cannot restart execution or replace debug.
        illegal=0; instr_class=IC_ALU; rd_write=1;
        imem_req_ready=1; imem_rsp_valid=1; dmem_req_ready=1; dmem_rsp_valid=1;
        pc=32'hdeadbeec; instr_pc=32'hcafebabc;
        repeat(3) begin
            #1;
            must(!imem_req_valid && !dmem_req_valid && !imem_rsp_ready && !dmem_rsp_ready &&
                 !pc_we && !reg_we && !ir_we && !mdr_we && !instr_done,"halt remains inactive");
            tick;
            must(halt_cause==cause && fault_pc==expected_pc && fault_addr==expected_addr,
                 "fault record sticky");
            @(negedge clk);
        end
        cases++;
    endtask

    task automatic run_memory(input logic write_mode,
                              input int req_delay,input int rsp_delay,
                              input logic response_error);
        if (write_mode) begin_instruction(IC_STORE,0,MEM_WORD,req_delay,rsp_delay);
        else begin_instruction(IC_LOAD,1,MEM_WORD,req_delay,rsp_delay);
        #1; must(ab_we && !pc_we,"memory decode operands");
        tick; must(state==ST_ADDR_EXEC && aluout_we,"address execute");
        tick; must(state==ST_MEM_CHECK && !dmem_req_valid,"pre-request check");
        tick;
        if (write_mode) must(state==ST_STORE_WAIT,"store wait state");
        else must(state==ST_LOAD_WAIT,"load wait state");
        @(negedge clk);
        repeat(req_delay) begin
            #1;
            must(dmem_req_valid && !dmem_rsp_ready && !mem_pending,"data request stall");
            must(dmem_req_write==write_mode && dmem_req_addr==32'h10000004,"data request fields");
            tick; @(negedge clk);
        end
        dmem_req_ready=1; dmem_rsp_valid=1;
        #1; must(!dmem_rsp_ready && !mdr_we && !pc_we,"no same-edge data response");
        tick; must(mem_pending && !dmem_req_valid,"data accepted once");
        @(negedge clk); dmem_req_ready=0; dmem_rsp_valid=0;
        repeat(rsp_delay) begin
            #1;
            must(dmem_rsp_ready && !dmem_req_valid && !reg_we && !pc_we,"data response wait");
            tick; @(negedge clk);
        end
        dmem_rsp_valid=1; dmem_rsp_err=response_error;
        #1; must(dmem_rsp_ready,"response handshake including error");
        if (response_error) begin
            if (write_mode) expect_stop(HALT_STORE_ACCESS,32'h100,32'h10000004);
            else expect_stop(HALT_LOAD_ACCESS,32'h100,32'h10000004);
            must(!mem_pending,"error response clears pending");
        end else if (write_mode) begin
            must(pc_we && instr_done && !reg_we && !mdr_we,"store completes on response");
            tick; must(state==ST_FETCH && !mem_pending,"store complete");
            @(negedge clk); dmem_rsp_valid=0;
            cases++;
        end else begin
            must(mdr_we && !reg_we && !pc_we,"load captures before writeback");
            tick; must(state==ST_LOAD_WB && !mem_pending,"load writeback state");
            @(negedge clk); dmem_rsp_valid=0;
            #1; must(reg_we && pc_we && instr_done,"load writeback enables");
            tick; must(state==ST_FETCH,"load complete");
            cases++;
        end
    endtask

    // Protocol and safety monitor. Evaluate actions before sequential updates.
    always @(posedge clk) begin
        if (rst) begin
            score_pending=0; score_data=0; stalled_i=0; stalled_d=0;
        end else begin
            must(mem_pending===score_pending,"pending matches accepted transactions");
            must(!(imem_req_valid && dmem_req_valid),"one request channel at a time");
            must(!(imem_rsp_ready && dmem_rsp_ready),"one response channel at a time");
            must(pc_we===instr_done,"commit indicator equals PC enable");
            if (stalled_i) must(imem_req_valid && imem_req_addr==held_i_addr,"held instruction request");
            if (stalled_d) must(dmem_req_valid && dmem_req_addr==held_d_addr && dmem_req_write==held_d_write,
                                "held data request");
            if (imem_req_valid && imem_req_ready) begin
                must(!score_pending,"no duplicate fetch acceptance"); score_pending=1; score_data=0;
            end
            if (dmem_req_valid && dmem_req_ready) begin
                must(!score_pending,"no duplicate data acceptance"); score_pending=1; score_data=1;
            end
            if (imem_rsp_ready && imem_rsp_valid) begin
                must(score_pending && !score_data,"fetch response has owner"); score_pending=0;
            end
            if (dmem_rsp_ready && dmem_rsp_valid) begin
                must(score_pending && score_data,"data response has owner"); score_pending=0;
            end
            if (ir_we) must(imem_rsp_ready && imem_rsp_valid && !imem_rsp_err,"IR only on success");
            if (mdr_we) must(dmem_rsp_ready && dmem_rsp_valid && !dmem_rsp_err,"MDR only on success");
            if (reg_we) must(rd_write && (state==ST_ALU_WB || state==ST_LOAD_WB || state==ST_JUMP_COMMIT),
                             "RF write only at allowed commit");
            stalled_i=imem_req_valid && !imem_req_ready;
            stalled_d=dmem_req_valid && !dmem_req_ready;
            held_i_addr=imem_req_addr; held_d_addr=dmem_req_addr; held_d_write=dmem_req_write;
        end
    end

    initial begin
        rst=1; illegal=0; rd_write=0; instr_class=IC_INVALID; mem_size=MEM_WORD;
        pc=0; instr_pc=0; mem_addr=0; target_addr=0; branch_taken=0;
        imem_req_ready=0; imem_rsp_valid=0; imem_rsp_err=0;
        dmem_req_ready=0; dmem_rsp_valid=0; dmem_rsp_err=0;

        for (rq=0; rq<4; rq=rq+1) begin
            for (rs=0; rs<4; rs=rs+1) begin
                begin_instruction(IC_ALU,1,MEM_WORD,rq,rs);
                #1; must(ab_we,"ALU decode operands");
                tick; must(state==ST_ALU_EXEC && aluout_we && !reg_we,"ALU execute");
                tick; must(state==ST_ALU_WB && reg_we && pc_we && pc_sel==PC_SEQ,"ALU writeback");
                tick; must(state==ST_FETCH,"ALU returns to fetch"); cases++;
                run_memory(0,rq,rs,0);
                run_memory(1,rq,rs,0);
            end
        end
        run_memory(0,2,3,1);
        run_memory(1,3,2,1);

        begin_instruction(IC_ALU,0,MEM_WORD,0,0);
        tick; tick; must(!reg_we && pc_we,"no-write ALU still advances"); tick; cases++;
        begin_instruction(IC_FENCE,0,MEM_WORD,1,1);
        tick; must(state==ST_FENCE_COMMIT && !reg_we && pc_we && !mem_pending,"fence complete");
        tick; must(state==ST_FETCH,"fence returns"); cases++;

        for (k=0; k<3; k=k+1) begin
            begin_instruction(IC_BRANCH,0,MEM_WORD,0,1);
            branch_taken=(k!=0); target_addr=(k==1)?32'h200:32'h202;
            tick; must(aluout_we && branch_taken_we && !reg_we,"branch execute captures");
            tick; must(state==ST_BR_COMMIT,"branch commit state");
            if (k==2) expect_stop(HALT_INSTR_ALIGN,32'h100,32'h202);
            else begin
                must(pc_we && !reg_we && pc_sel==((k==0)?PC_SEQ:PC_TARGET),"branch selection");
                tick; must(state==ST_FETCH,"branch complete"); cases++;
            end
        end
        for (k=0; k<4; k=k+1) begin
            begin_instruction((k<2)?IC_JAL:IC_JALR,1,MEM_WORD,1,0);
            target_addr=(k%2==0)?32'h200:32'h202;
            tick; must(aluout_we && !reg_we,"jump execute");
            tick; must(state==ST_JUMP_COMMIT,"jump commit state");
            if (k%2==1) expect_stop(HALT_INSTR_ALIGN,32'h100,32'h202);
            else begin
                must(pc_we && reg_we && pc_sel==PC_TARGET,"jump commits link and PC");
                tick; cases++;
            end
        end

        begin_instruction(IC_ALU,1,MEM_WORD,0,0); illegal=1;
        expect_stop(HALT_ILLEGAL,32'h100,0);
        begin_instruction(IC_INVALID,0,MEM_WORD,0,0);
        expect_stop(HALT_ILLEGAL,32'h100,0);
        begin_instruction(IC_ECALL,0,MEM_WORD,0,0);
        expect_stop(HALT_ECALL,32'h100,0);
        begin_instruction(IC_EBREAK,0,MEM_WORD,0,0);
        expect_stop(HALT_EBREAK,32'h100,0);

        reset_all; pc=32'h102; instr_pc=32'h80;
        expect_stop(HALT_INSTR_ALIGN,32'h102,32'h102);
        reset_all; pc=32'h300; instr_pc=32'h80;
        imem_req_ready=1; tick;
        @(negedge clk); imem_req_ready=0; imem_rsp_valid=1; imem_rsp_err=1;
        #1; must(imem_rsp_ready,"failed fetch response accepted");
        expect_stop(HALT_FETCH_ACCESS,32'h300,32'h300);
        must(!mem_pending,"failed fetch clears pending");

        for (k=0; k<4; k=k+1) begin
            begin_instruction((k<2)?IC_LOAD:IC_STORE,k<2,(k%2==0)?MEM_HALF:MEM_WORD,0,0);
            mem_addr=(k%2==0)?32'h10000001:32'h10000002;
            tick; tick;
            if (k<2) expect_stop(HALT_LOAD_ALIGN,32'h100,mem_addr);
            else expect_stop(HALT_STORE_ALIGN,32'h100,mem_addr);
        end
        for (k=0; k<4; k=k+1) begin
            begin_instruction((k<2)?IC_LOAD:IC_STORE,k<2,(k%2==0)?MEM_BYTE:MEM_HALF,0,0);
            mem_addr=32'h20000000; tick; tick;
            if (k<2) expect_stop(HALT_LOAD_ACCESS,32'h100,32'h20000000);
            else expect_stop(HALT_STORE_ACCESS,32'h100,32'h20000000);
        end
        begin_instruction(IC_LOAD,1,MEM_HALF,0,0);
        mem_addr=32'h20000001; tick; tick;
        expect_stop(HALT_LOAD_ALIGN,32'h100,32'h20000001);

        // Byte address stays raw for faults; external bus address is word aligned.
        begin_instruction(IC_LOAD,1,MEM_BYTE,0,0);
        mem_addr=32'h10000003; tick; tick; tick;
        must(dmem_req_valid && dmem_req_addr==32'h10000000,"byte bus address aligned");
        @(negedge clk); dmem_req_ready=1; tick;
        @(negedge clk); dmem_req_ready=0; dmem_rsp_valid=1; dmem_rsp_err=1;
        expect_stop(HALT_LOAD_ACCESS,32'h100,32'h10000003);

        // Reset naturally reached states, including commit states before their edge.
        for (s=0; s<15; s=s+1) begin
            wanted=cpu_state_t'(s);
            case (wanted)
                ST_ADDR_EXEC,ST_MEM_CHECK,ST_LOAD_WAIT,ST_LOAD_WB: chosen=IC_LOAD;
                ST_STORE_WAIT: chosen=IC_STORE;
                ST_BR_EXEC,ST_BR_COMMIT: chosen=IC_BRANCH;
                ST_JUMP_EXEC,ST_JUMP_COMMIT: chosen=IC_JAL;
                ST_FENCE_COMMIT: chosen=IC_FENCE;
                ST_HALTED: chosen=IC_EBREAK;
                default: chosen=IC_ALU;
            endcase
            if (wanted==ST_FETCH) reset_all;
            else begin
                begin_instruction(chosen,1,MEM_WORD,0,0);
                dmem_req_ready=1; dmem_rsp_valid=1;
                while (state!=wanted) tick;
            end
            if (clk) @(negedge clk);
            rst=1;
            #1; must(state==wanted,"reset synchronous state before edge");
            must(!pc_we && !reg_we && !imem_req_valid && !dmem_req_valid &&
                 !imem_rsp_ready && !dmem_rsp_ready,"reset suppresses actions");
            tick;
            must(state==ST_FETCH && !mem_pending && halt_cause==HALT_NONE,"reset every state");
            cases++;
        end
        // Reset after an accepted instruction request.
        reset_all; imem_req_ready=1; tick;
        must(mem_pending,"fetch pending before reset");
        @(negedge clk); rst=1; imem_req_ready=0;
        tick; must(state==ST_FETCH && !mem_pending,"reset cancels fetch tracking"); cases++;
        // Reset after an accepted data request.
        begin_instruction(IC_LOAD,1,MEM_WORD,0,0); tick; tick; tick;
        @(negedge clk); dmem_req_ready=1; tick;
        must(mem_pending,"data pending before reset");
        @(negedge clk); rst=1; dmem_req_ready=0;
        tick; must(state==ST_FETCH && !mem_pending && !mdr_we,"reset cancels data tracking"); cases++;

        $display("ALL %0d CONTROL FSM SCENARIOS PASSED (%0d checks)",cases,checks);
        $finish;
    end
    initial begin #100000; $fatal(1,"TIMEOUT tb_control_fsm"); end
endmodule
