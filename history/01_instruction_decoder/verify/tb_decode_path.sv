module tb_decode_path;
    timeunit 1ns;
    timeprecision 1ps;
    import fault_v_pkg::*;
    logic [31:0] instruction;
    logic [4:0] rs1_addr, rs2_addr, rd_addr;
    instr_class_t instr_class;
    alu_op_t alu_op;
    imm_sel_t imm_sel;
    alu_src_a_t alu_src_a;
    alu_src_b_t alu_src_b;
    branch_op_t branch_op;
    mem_size_t mem_size;
    logic load_unsigned, rd_write, illegal;
    wb_sel_t wb_sel;
    decoder dut (
        .instruction(instruction),
        .rs1_addr(rs1_addr), .rs2_addr(rs2_addr), .rd_addr(rd_addr),
        .instr_class(instr_class), .alu_op(alu_op), .imm_sel(imm_sel),
        .alu_src_a(alu_src_a), .alu_src_b(alu_src_b), .branch_op(branch_op),
        .mem_size(mem_size), .load_unsigned(load_unsigned),
        .rd_write(rd_write), .wb_sel(wb_sel), .illegal(illegal)
    );

    logic [31:0] a_value,b_value,instr_pc,imm,alu_a,alu_b;
    logic [31:0] result,target_value,wb_candidate;
    int test_count=0;
    imm_gen u_imm(.instruction(instruction),.imm_sel(imm_sel),.imm(imm));
    alu u_alu(.a(alu_a),.b(alu_b),.alu_op(alu_op),.result(result));
    always_comb begin
        case (alu_src_a)
            ALU_A_REG: alu_a=a_value;
            ALU_A_PC: alu_a=instr_pc;
            default: alu_a=32'b0;
        endcase
        alu_b=(alu_src_b==ALU_B_REG)?b_value:imm;
        target_value=(instr_class==IC_JALR)?(result&32'hfffffffe):result;
        wb_candidate=32'b0;
        if (rd_write && !illegal) begin
            case (wb_sel)
                WB_ALU: wb_candidate=result;
                WB_PC4: wb_candidate=instr_pc+32'd4;
                default: wb_candidate=32'b0; // No memory return data in this test.
            endcase
        end
    end
    task automatic check(input string label_text,
                         input logic [31:0] inst,av,bv,ip,
                         input logic [31:0] expected_imm,expected_result,
                         input logic [31:0] expected_target,expected_wb);
        instruction=inst; a_value=av; b_value=bv; instr_pc=ip;
        #10;
        if ((imm !== expected_imm) || (result !== expected_result) ||
            (target_value !== expected_target) || (wb_candidate !== expected_wb))
            $fatal(1,"FAIL %s imm=%h/%h result=%h/%h target=%h/%h wb=%h/%h",label_text,imm,expected_imm,result,expected_result,target_value,expected_target,wb_candidate,expected_wb);
        test_count++;
        $display("PASS %0d: %s imm=%h result=%h target=%h wb=%h",test_count,label_text,imm,result,target_value,wb_candidate);
    endtask
    initial begin
        check("ADD",32'h007302b3,32'h00000005,32'h00000003,32'h00000100,32'h00000000,32'h00000008,32'h00000008,32'h00000008);
        check("SUB negative",32'h407302b3,32'h00000003,32'h00000005,32'h00000100,32'h00000000,32'hfffffffe,32'hfffffffe,32'hfffffffe);
        check("SLL mask",32'h007312b3,32'h00000001,32'h00000020,32'h00000100,32'h00000000,32'h00000001,32'h00000001,32'h00000001);
        check("SLT signed",32'h007322b3,32'hffffffff,32'h00000001,32'h00000100,32'h00000000,32'h00000001,32'h00000001,32'h00000001);
        check("SLTU unsigned",32'h007332b3,32'hffffffff,32'h00000001,32'h00000100,32'h00000000,32'h00000000,32'h00000000,32'h00000000);
        check("XOR",32'h007342b3,32'h0000000a,32'h0000000c,32'h00000100,32'h00000000,32'h00000006,32'h00000006,32'h00000006);
        check("SRL",32'h007352b3,32'h80000000,32'h00000001,32'h00000100,32'h00000000,32'h40000000,32'h40000000,32'h40000000);
        check("SRA",32'h407352b3,32'h80000000,32'h00000001,32'h00000100,32'h00000000,32'hc0000000,32'hc0000000,32'hc0000000);
        check("OR",32'h007362b3,32'h0000000a,32'h0000000c,32'h00000100,32'h00000000,32'h0000000e,32'h0000000e,32'h0000000e);
        check("AND",32'h007372b3,32'h0000000a,32'h0000000c,32'h00000100,32'h00000000,32'h00000008,32'h00000008,32'h00000008);
        check("ADDI negative",32'hffc30293,32'h0000000a,32'hdeadbeef,32'h00000100,32'hfffffffc,32'h00000006,32'h00000006,32'h00000006);
        check("SLTI signed",32'hffc32293,32'hfffffff8,32'h00000000,32'h00000100,32'hfffffffc,32'h00000001,32'h00000001,32'h00000001);
        check("SLTIU sign-extended immediate",32'hffc33293,32'h00000000,32'h00000000,32'h00000100,32'hfffffffc,32'h00000001,32'h00000001,32'h00000001);
        check("XORI negative",32'hffc34293,32'h12345678,32'h00000000,32'h00000100,32'hfffffffc,32'hedcba984,32'hedcba984,32'hedcba984);
        check("ORI negative",32'hffc36293,32'h12345678,32'h00000000,32'h00000100,32'hfffffffc,32'hfffffffc,32'hfffffffc,32'hfffffffc);
        check("ANDI negative",32'hffc37293,32'h1234567b,32'h00000000,32'h00000100,32'hfffffffc,32'h12345678,32'h12345678,32'h12345678);
        check("SLLI 31",32'h01f31293,32'h00000001,32'h00000000,32'h00000100,32'h0000001f,32'h80000000,32'h80000000,32'h80000000);
        check("SRLI 31",32'h01f35293,32'h80000000,32'h00000000,32'h00000100,32'h0000001f,32'h00000001,32'h00000001,32'h00000001);
        check("SRAI 31",32'h41f35293,32'h80000000,32'h00000000,32'h00000100,32'h0000041f,32'hffffffff,32'hffffffff,32'hffffffff);
        check("LUI",32'h123452b7,32'hdeadbeef,32'h00000000,32'h00000100,32'h12345000,32'h12345000,32'h12345000,32'h12345000);
        check("AUIPC",32'h12345297,32'hdeadbeef,32'h00000000,32'h00000100,32'h12345000,32'h12345100,32'h12345100,32'h12345100);
        check("Branch backward target",32'hfe730ee3,32'hdeadbeef,32'h00000000,32'h00000100,32'hfffffffc,32'h000000fc,32'h000000fc,32'h00000000);
        check("JAL target and link",32'hffdff2ef,32'h00000000,32'h00000000,32'h00000100,32'hfffffffc,32'h000000fc,32'h000000fc,32'h00000104);
        check("JALR clear bit zero",32'h000302e7,32'h00000101,32'h00000000,32'h00000100,32'h00000000,32'h00000101,32'h00000100,32'h00000104);
        check("JALR negative offset",32'hffc302e7,32'h00000200,32'h00000000,32'h00000100,32'hfffffffc,32'h000001fc,32'h000001fc,32'h00000104);
        check("LW effective address",32'hffc32283,32'h10000008,32'h00000000,32'h00000100,32'hfffffffc,32'h10000004,32'h10000004,32'h00000000);
        check("SW effective address",32'hfe732e23,32'h10000008,32'h12345678,32'h00000100,32'hfffffffc,32'h10000004,32'h10000004,32'h00000000);
        check("FENCE safe controls",32'h0ff0000f,32'hdeadbeef,32'hffffffff,32'h00000100,32'h00000000,32'h00000000,32'h00000000,32'h00000000);
        check("ECALL safe controls",32'h00000073,32'hdeadbeef,32'hffffffff,32'h00000100,32'h00000000,32'h00000000,32'h00000000,32'h00000000);
        check("EBREAK safe controls",32'h00100073,32'hdeadbeef,32'hffffffff,32'h00000100,32'h00000000,32'h00000000,32'h00000000,32'h00000000);
        check("Illegal safe controls",32'hffffffff,32'hdeadbeef,32'hffffffff,32'h00000100,32'h00000000,32'h00000000,32'h00000000,32'h00000000);
        check("ADDI after illegal",32'hffc30293,32'h0000000a,32'h00000000,32'h00000100,32'hfffffffc,32'h00000006,32'h00000006,32'h00000006);
        check("ADDI overflow wraps",32'h00130293,32'hffffffff,32'h00000000,32'h00000100,32'h00000001,32'h00000000,32'h00000000,32'h00000000);
        $display("ALL %0d DECODE PATH CASES PASSED",test_count);
        $finish;
    end
    initial begin
        #10000;
        $fatal(1,"TIMEOUT tb_decode_path");
    end
endmodule
