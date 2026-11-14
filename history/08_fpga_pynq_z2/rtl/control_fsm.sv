`timescale 1ns/1ps
module control_fsm (
    input logic clk, rst,
    // Decoder outputs. IR and decoded controls must stay stable until commit.
    input fault_v_pkg::instr_class_t instr_class,
    input logic illegal, rd_write,
    input fault_v_pkg::mem_size_t mem_size,
    // Datapath state: current fetch PC, instruction PC, raw data address,
    // and the already processed branch/jump target (JALR bit 0 cleared).
    input logic [31:0] pc, instr_pc, mem_addr, target_addr,
    input logic branch_taken,

    // Separate instruction and data request/response channels.
    output logic imem_req_valid,
    input logic imem_req_ready,
    output logic [31:0] imem_req_addr,
    input logic imem_rsp_valid, imem_rsp_err,
    output logic imem_rsp_ready,
    output logic dmem_req_valid,
    input logic dmem_req_ready,
    output logic dmem_req_write,
    output logic [31:0] dmem_req_addr,
    input logic dmem_rsp_valid, dmem_rsp_err,
    output logic dmem_rsp_ready,

    // Datapath enables, all sampled on rising edges.
    output logic ir_we, instr_pc_we, ab_we, aluout_we,
    output logic branch_taken_we, mdr_we, reg_we, pc_we,
    output fault_v_pkg::pc_sel_t pc_sel,
    output logic instr_done,

    // Observable state and sticky debug information.
    output fault_v_pkg::cpu_state_t state,
    output logic mem_pending, halted,
    output fault_v_pkg::halt_cause_t halt_cause,
    output logic [31:0] fault_pc, fault_addr
);
    import fault_v_pkg::*;
    cpu_state_t next_state;
    logic pending_next, halt_event, data_misaligned, narrow_mmio;
    halt_cause_t event_cause;
    logic [31:0] event_pc, event_addr;

    assign imem_req_addr=pc;
    assign dmem_req_addr={mem_addr[31:2],2'b00};
    assign halted=(state==ST_HALTED);

    always_comb begin
        data_misaligned=1'b0;
        case (mem_size)
            MEM_BYTE: data_misaligned=1'b0;
            MEM_HALF: data_misaligned=mem_addr[0];
            MEM_WORD: data_misaligned=|mem_addr[1:0];
            default: data_misaligned=1'b1;
        endcase
        // The agreed first MMIO page permits word accesses only.
        narrow_mmio=(mem_addr[31:12]==20'h20000) && (mem_size!=MEM_WORD);
    end

    always_comb begin
        next_state=state;
        pending_next=mem_pending;
        imem_req_valid=0; imem_rsp_ready=0;
        dmem_req_valid=0; dmem_req_write=0; dmem_rsp_ready=0;
        ir_we=0; instr_pc_we=0; ab_we=0; aluout_we=0;
        branch_taken_we=0; mdr_we=0; reg_we=0; pc_we=0;
        pc_sel=PC_SEQ; instr_done=0;
        halt_event=0; event_cause=HALT_NONE;
        event_pc=instr_pc; event_addr=0;

        case (state)
            ST_FETCH: begin
                if (!mem_pending) begin
                    if (pc[1:0]!=2'b00) begin
                        halt_event=1; event_cause=HALT_INSTR_ALIGN;
                        event_pc=pc; event_addr=pc;
                    end else begin
                        imem_req_valid=1;
                        if (imem_req_ready) pending_next=1;
                    end
                end else begin
                    imem_rsp_ready=1;
                    if (imem_rsp_valid) begin
                        pending_next=0;
                        if (imem_rsp_err) begin
                            halt_event=1; event_cause=HALT_FETCH_ACCESS;
                            event_pc=pc; event_addr=pc;
                        end else begin
                            ir_we=1; instr_pc_we=1; next_state=ST_DECODE;
                        end
                    end
                end
            end
            ST_DECODE: begin
                if (illegal) begin
                    halt_event=1; event_cause=HALT_ILLEGAL;
                end else begin
                    case (instr_class)
                        IC_ALU: begin ab_we=1; next_state=ST_ALU_EXEC; end
                        IC_LOAD, IC_STORE: begin ab_we=1; next_state=ST_ADDR_EXEC; end
                        IC_BRANCH: begin ab_we=1; next_state=ST_BR_EXEC; end
                        IC_JAL, IC_JALR: begin ab_we=1; next_state=ST_JUMP_EXEC; end
                        IC_FENCE: next_state=ST_FENCE_COMMIT;
                        IC_ECALL: begin halt_event=1; event_cause=HALT_ECALL; end
                        IC_EBREAK: begin halt_event=1; event_cause=HALT_EBREAK; end
                        default: begin halt_event=1; event_cause=HALT_ILLEGAL; end
                    endcase
                end
            end
            ST_ALU_EXEC: begin aluout_we=1; next_state=ST_ALU_WB; end
            ST_ALU_WB: begin
                reg_we=rd_write; pc_we=1; instr_done=1; next_state=ST_FETCH;
            end
            ST_ADDR_EXEC: begin aluout_we=1; next_state=ST_MEM_CHECK; end
            ST_MEM_CHECK: begin
                // Misalignment has priority over unsupported narrow MMIO.
                if (data_misaligned) begin
                    halt_event=1; event_addr=mem_addr;
                    if (instr_class==IC_LOAD) event_cause=HALT_LOAD_ALIGN;
                    else event_cause=HALT_STORE_ALIGN;
                end else if (narrow_mmio) begin
                    halt_event=1; event_addr=mem_addr;
                    if (instr_class==IC_LOAD) event_cause=HALT_LOAD_ACCESS;
                    else event_cause=HALT_STORE_ACCESS;
                end else if (instr_class==IC_LOAD) next_state=ST_LOAD_WAIT;
                else if (instr_class==IC_STORE) next_state=ST_STORE_WAIT;
                else begin halt_event=1; event_cause=HALT_INTERNAL; end
            end
            ST_LOAD_WAIT, ST_STORE_WAIT: begin
                dmem_req_write=(state==ST_STORE_WAIT);
                if (!mem_pending) begin
                    dmem_req_valid=1;
                    if (dmem_req_ready) pending_next=1;
                end else begin
                    dmem_rsp_ready=1;
                    if (dmem_rsp_valid) begin
                        pending_next=0;
                        if (dmem_rsp_err) begin
                            halt_event=1; event_addr=mem_addr;
                            if (state==ST_LOAD_WAIT) event_cause=HALT_LOAD_ACCESS;
                            else event_cause=HALT_STORE_ACCESS;
                        end else if (state==ST_LOAD_WAIT) begin
                            mdr_we=1; next_state=ST_LOAD_WB;
                        end else begin
                            pc_we=1; instr_done=1; next_state=ST_FETCH;
                        end
                    end
                end
            end
            ST_LOAD_WB: begin
                reg_we=rd_write; pc_we=1; instr_done=1; next_state=ST_FETCH;
            end
            ST_BR_EXEC: begin
                aluout_we=1; branch_taken_we=1; next_state=ST_BR_COMMIT;
            end
            ST_BR_COMMIT: begin
                if (branch_taken && (target_addr[1:0]!=2'b00)) begin
                    halt_event=1; event_cause=HALT_INSTR_ALIGN; event_addr=target_addr;
                end else begin
                    if (branch_taken) pc_sel=PC_TARGET;
                    pc_we=1; instr_done=1; next_state=ST_FETCH;
                end
            end
            ST_JUMP_EXEC: begin aluout_we=1; next_state=ST_JUMP_COMMIT; end
            ST_JUMP_COMMIT: begin
                if (target_addr[1:0]!=2'b00) begin
                    halt_event=1; event_cause=HALT_INSTR_ALIGN; event_addr=target_addr;
                end else begin
                    pc_sel=PC_TARGET; reg_we=rd_write;
                    pc_we=1; instr_done=1; next_state=ST_FETCH;
                end
            end
            ST_FENCE_COMMIT: begin
                if (!mem_pending) begin
                    pc_we=1; instr_done=1; next_state=ST_FETCH;
                end
            end
            ST_HALTED: begin end
            default: begin halt_event=1; event_cause=HALT_INTERNAL; end
        endcase

        if (halt_event) begin
            next_state=ST_HALTED;
            // An error response must still handshake before entering HALTED.
            imem_req_valid=0; dmem_req_valid=0;
            ir_we=0; instr_pc_we=0; ab_we=0; aluout_we=0;
            branch_taken_we=0; mdr_we=0; reg_we=0; pc_we=0; instr_done=0;
        end
        // Suppress external actions while reset is asserted; sequential reset
        // still takes effect only at the rising edge.
        if (rst) begin
            next_state=ST_FETCH; pending_next=0; halt_event=0;
            imem_req_valid=0; imem_rsp_ready=0;
            dmem_req_valid=0; dmem_req_write=0; dmem_rsp_ready=0;
            ir_we=0; instr_pc_we=0; ab_we=0; aluout_we=0;
            branch_taken_we=0; mdr_we=0; reg_we=0; pc_we=0; instr_done=0;
            pc_sel=PC_SEQ;
        end
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state<=ST_FETCH; mem_pending<=0;
            halt_cause<=HALT_NONE; fault_pc<=0; fault_addr<=0;
        end else begin
            state<=next_state; mem_pending<=pending_next;
            if (halt_event) begin
                halt_cause<=event_cause; fault_pc<=event_pc; fault_addr<=event_addr;
            end
        end
    end
endmodule
