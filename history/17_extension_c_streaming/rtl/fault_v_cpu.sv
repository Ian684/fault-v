`timescale 1ns/1ps
module fault_v_cpu (
    input logic clk, rst,
    output logic imem_req_valid,
    input logic imem_req_ready,
    output logic [31:0] imem_req_addr,
    input logic imem_rsp_valid, imem_rsp_err,
    input logic [31:0] imem_rsp_data,
    output logic imem_rsp_ready,
    // Data request/response interface: aligned word data with byte strobes.
    output logic dmem_req_valid,
    input logic dmem_req_ready,
    output logic dmem_req_write,
    output logic [31:0] dmem_req_addr,dmem_req_wdata,
    output logic [3:0] dmem_req_wstrb,
    input logic dmem_rsp_valid,dmem_rsp_err,
    input logic [31:0] dmem_rsp_data,
    output logic dmem_rsp_ready,
    output logic halted,
    output fault_v_pkg::halt_cause_t halt_cause,
    output logic [31:0] fault_pc,fault_addr,pc,
    output fault_v_pkg::cpu_state_t state,
    // Combinational commit trace, sampled at the same rising edge as writeback.
    // These are project-specific signals, not a full RVFI implementation.
    output logic retire_valid,retire_rd_we,
    output logic [31:0] retire_pc,retire_instruction,retire_rd_data,
    output logic [4:0] retire_rd_addr
);
    import fault_v_pkg::*;
    logic [31:0] ir,instr_pc,a_reg,b_reg,aluout,mdr;
    logic [31:0] custom_result, custom_rsp_result,custom_acc;
    logic custom_acc_we,custom_accumulate;
    logic [4:0] rf_rs2_addr;
    custom_op_t custom_op;
    logic custom_req_valid,custom_req_ready,custom_rsp_valid,custom_rsp_ready,custom_result_we;
    logic [31:0] rs1_data,rs2_data,imm,alu_a,alu_b,alu_result,pc_next;
    logic [4:0] rs1_addr,rs2_addr,rd_addr;
    instr_class_t instr_class;
    alu_op_t alu_op;
    imm_sel_t imm_sel;
    alu_src_a_t alu_src_a;
    alu_src_b_t alu_src_b;
    branch_op_t branch_op;
    mem_size_t mem_size;
    wb_sel_t wb_sel;
    pc_sel_t pc_sel;
    logic load_unsigned,rd_write,decode_illegal,core_illegal;
    logic ir_we,instr_pc_we,ab_we,aluout_we,branch_taken_we,mdr_we,reg_we,pc_we;
    logic instr_done,mem_pending,branch_taken,branch_condition;
    logic [31:0] wb_data,load_result,store_wdata;
    logic [3:0] store_wstrb;

    decoder u_decoder(.instruction(ir),.rs1_addr(rs1_addr),.rs2_addr(rs2_addr),.rd_addr(rd_addr),
        .instr_class(instr_class),.alu_op(alu_op),.imm_sel(imm_sel),
        .alu_src_a(alu_src_a),.alu_src_b(alu_src_b),.branch_op(branch_op),
        .mem_size(mem_size),.load_unsigned(load_unsigned),.rd_write(rd_write),
        .wb_sel(wb_sel),.custom_op(custom_op),.illegal(decode_illegal));
    assign core_illegal=decode_illegal;
    assign custom_accumulate=(custom_op==CUSTOM_DOT4ACC || custom_op==CUSTOM_MAC16);
    assign rf_rs2_addr=(state==ST_CUSTOM_ACC_READ)?rd_addr:rs2_addr;

    control_fsm u_control(.clk(clk),.rst(rst),.instr_class(instr_class),
        .illegal(core_illegal),.rd_write(rd_write),.mem_size(mem_size),
        .custom_accumulate(custom_accumulate),.custom_acc_we(custom_acc_we),
        .custom_req_valid(custom_req_valid),.custom_req_ready(custom_req_ready),
        .custom_rsp_valid(custom_rsp_valid),.custom_rsp_ready(custom_rsp_ready),.custom_result_we(custom_result_we),
        .pc(pc),.instr_pc(instr_pc),.mem_addr(aluout),.target_addr(aluout),.branch_taken(branch_taken),
        .imem_req_valid(imem_req_valid),.imem_req_ready(imem_req_ready),.imem_req_addr(imem_req_addr),
        .imem_rsp_valid(imem_rsp_valid),.imem_rsp_err(imem_rsp_err),.imem_rsp_ready(imem_rsp_ready),
        .dmem_req_valid(dmem_req_valid),.dmem_req_ready(dmem_req_ready),
        .dmem_req_write(dmem_req_write),.dmem_req_addr(dmem_req_addr),
        .dmem_rsp_valid(dmem_rsp_valid),.dmem_rsp_err(dmem_rsp_err),.dmem_rsp_ready(dmem_rsp_ready),
        .ir_we(ir_we),.instr_pc_we(instr_pc_we),.ab_we(ab_we),.aluout_we(aluout_we),
        .branch_taken_we(branch_taken_we),.mdr_we(mdr_we),.reg_we(reg_we),.pc_we(pc_we),
        .pc_sel(pc_sel),.instr_done(instr_done),.state(state),.mem_pending(mem_pending),
        .halted(halted),.halt_cause(halt_cause),.fault_pc(fault_pc),.fault_addr(fault_addr));
    custom_exec u_custom(.clk(clk),.rst(rst),.req_valid(custom_req_valid),.req_ready(custom_req_ready),
        .req_op(custom_op),.req_a(a_reg),.req_b(b_reg),.req_acc(custom_acc),.rsp_valid(custom_rsp_valid),
        .rsp_ready(custom_rsp_ready),.rsp_result(custom_rsp_result));
    regfile u_regfile(.clk(clk),.rst(rst),.rs1_addr(rs1_addr),.rs2_addr(rf_rs2_addr),
        .rs1_data(rs1_data),.rs2_data(rs2_data),.rd_we(reg_we),.rd_addr(rd_addr),.rd_data(wb_data));
    imm_gen u_imm(.instruction(ir),.imm_sel(imm_sel),.imm(imm));
    alu u_alu(.a(alu_a),.b(alu_b),.alu_op(alu_op),.result(alu_result));
    pc_reg u_pc(.clk(clk),.rst(rst),.pc_we(pc_we),.pc_next(pc_next),.pc(pc));

    branch_compare u_branch(.a(a_reg),.b(b_reg),.branch_op(branch_op),.taken(branch_condition));
    load_extract u_load(.word_data(mdr),.byte_offset(aluout[1:0]),.mem_size(mem_size),
        .load_unsigned(load_unsigned),.result(load_result));
    store_align u_store(.data(b_reg),.byte_offset(aluout[1:0]),.mem_size(mem_size),
        .wdata(store_wdata),.wstrb(store_wstrb));
    always_comb begin
        case (wb_sel)
            WB_PC4: wb_data=instr_pc+32'd4;
            WB_LOAD: wb_data=load_result;
            WB_CUSTOM: wb_data=custom_result;
            default: wb_data=aluout;
        endcase
    end
    always_comb begin
        case (alu_src_a)
            ALU_A_REG: alu_a=a_reg;
            ALU_A_PC: alu_a=instr_pc;
            default: alu_a=32'b0;
        endcase
        alu_b=(alu_src_b==ALU_B_REG)?b_reg:imm;
        pc_next=instr_pc+32'd4;
        if (pc_sel==PC_TARGET) pc_next=aluout;
    end
    always_ff @(posedge clk) begin
        if (rst) begin ir<=0; instr_pc<=0; a_reg<=0; b_reg<=0; aluout<=0; branch_taken<=0; mdr<=0; custom_result<=0; custom_acc<=0; end
        else begin
            if (ir_we) ir<=imem_rsp_data;
            if (instr_pc_we) instr_pc<=pc;
            if (ab_we) begin a_reg<=rs1_data; b_reg<=rs2_data; end
            if (aluout_we) begin
                if (instr_class==IC_JALR) aluout<={alu_result[31:1],1'b0};
                else aluout<=alu_result;
            end
            if (branch_taken_we) branch_taken<=branch_condition;
            if (mdr_we) mdr<=dmem_rsp_data;
            if (custom_result_we) custom_result<=custom_rsp_result;
            if(custom_acc_we)custom_acc<=rs2_data;
        end
    end
    assign dmem_req_wdata=(instr_class==IC_STORE)?store_wdata:32'b0;
    assign dmem_req_wstrb=(instr_class==IC_STORE)?store_wstrb:4'b0;
    assign retire_valid=instr_done;
    assign retire_pc=instr_pc;
    assign retire_instruction=ir;
    assign retire_rd_we=instr_done && reg_we && (rd_addr!=0);
    assign retire_rd_addr=retire_rd_we?rd_addr:5'b0;
    assign retire_rd_data=retire_rd_we?wb_data:32'b0;
endmodule


