module tb_decoder;
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

    int test_count=0;
    bit verbose=1;
    localparam logic [23:0] SAFE=24'h001441;
    logic [23:0] golden;
    logic [31:0] word_value;
    logic [4:0] expected_rs2;
    integer f7,f3,sh,im,r,fm;

    // Golden controls are constants from the written test specification.
    // Order: class, alu, imm, src_a, src_b, branch, size, unsigned, write, wb, illegal.
    task automatic check(input string label_text,
                         input logic [31:0] inst,
                         input logic [23:0] expected);
        logic [23:0] observed;
        instruction=inst;
        #1;
        observed={instr_class,alu_op,imm_sel,alu_src_a,alu_src_b,
                  branch_op,mem_size,load_unsigned,rd_write,wb_sel,illegal};
        if (observed !== expected)
            $fatal(1,"FAIL %s inst=%h controls=%h expected=%h",label_text,inst,observed,expected);
        if ((rs1_addr !== inst[19:15]) || (rs2_addr !== inst[24:20]) || (rd_addr !== inst[11:7]))
            $fatal(1,"FAIL %s register fields rs1=%0d rs2=%0d rd=%0d",label_text,rs1_addr,rs2_addr,rd_addr);
        test_count++;
        if (verbose) $display("PASS %0d: %s inst=%h controls=%h",test_count,label_text,inst,observed);
    endtask

    initial begin
        check("ADD",32'h007302b3,24'h100048);
        check("SUB",32'h407302b3,24'h110048);
        check("SLL",32'h007312b3,24'h150048);
        check("SLT",32'h007322b3,24'h180048);
        check("SLTU",32'h007332b3,24'h190048);
        check("XOR",32'h007342b3,24'h140048);
        check("SRL",32'h007352b3,24'h160048);
        check("SRA",32'h407352b3,24'h170048);
        check("OR",32'h007362b3,24'h130048);
        check("AND",32'h007372b3,24'h120048);
        check("ADDI",32'hffc30293,24'h102448);
        check("SLTI",32'hffc32293,24'h182448);
        check("SLTIU",32'hffc33293,24'h192448);
        check("XORI",32'hffc34293,24'h142448);
        check("ORI",32'hffc36293,24'h132448);
        check("ANDI",32'hffc37293,24'h122448);
        check("SLLI",32'h01f31293,24'h152448);
        check("SRLI",32'h01f35293,24'h162448);
        check("SRAI",32'h41f35293,24'h172448);
        check("LUI",32'h123452b7,24'h109448);
        check("AUIPC",32'h12345297,24'h108c48);
        check("BEQ",32'hfe730ee3,24'h406cc0);
        check("BNE",32'hfe731ee3,24'h406d40);
        check("BLT",32'hfe734ee3,24'h406dc0);
        check("BGE",32'hfe735ee3,24'h406e40);
        check("BLTU",32'hfe736ee3,24'h406ec0);
        check("BGEU",32'hfe737ee3,24'h406f40);
        check("JAL",32'hffdff2ef,24'h50ac4c);
        check("JALR",32'hffc302e7,24'h60244c);
        check("LB",32'hffc30283,24'h20240a);
        check("LH",32'hffc31283,24'h20242a);
        check("LW",32'hffc32283,24'h20244a);
        check("LBU",32'hffc34283,24'h20241a);
        check("LHU",32'hffc35283,24'h20243a);
        check("SB",32'hfe730e23,24'h304400);
        check("SH",32'hfe731e23,24'h304420);
        check("SW",32'hfe732e23,24'h304440);
        check("FENCE",32'h0ff0000f,24'h701440);
        check("ECALL",32'h00000073,24'h801440);
        check("EBREAK",32'h00100073,24'h901440);
        verbose=0;

        // All 128 funct7 values x all eight funct3 values for opcode 0x33.
        for (f7=0; f7<128; f7++) begin
            for (f3=0; f3<8; f3++) begin
                golden=SAFE;
                case ({f7[6:0],f3[2:0]})
                    10'h000: golden=24'h100048;
                    10'h100: golden=24'h110048;
                    10'h001: golden=24'h150048;
                    10'h002: golden=24'h180048;
                    10'h003: golden=24'h190048;
                    10'h004: golden=24'h140048;
                    10'h005: golden=24'h160048;
                    10'h105: golden=24'h170048;
                    10'h006: golden=24'h130048;
                    10'h007: golden=24'h120048;
                    default: begin end
                endcase
                word_value={f7[6:0],5'd7,5'd6,f3[2:0],5'd5,7'h33};
                check("R encoding sweep",word_value,golden);
            end
        end

        // RV32 immediate shifts: all upper seven bits and all 32 shift amounts.
        for (f7=0; f7<128; f7++) begin
            for (sh=0; sh<32; sh++) begin
                golden=SAFE;
                if (f7==0) golden=24'h152448;
                check("SLLI encoding sweep",{f7[6:0],sh[4:0],5'd6,3'b001,5'd5,7'h13},golden);
                golden=SAFE;
                if (f7==0) golden=24'h162448;
                else if (f7==32) golden=24'h172448;
                check("SRLI/SRAI encoding sweep",{f7[6:0],sh[4:0],5'd6,3'b101,5'd5,7'h13},golden);
            end
        end

        // No funct7 restriction on the six non-shift I-type operations.
        for (im=0; im<4096; im++) begin
            check("ADDI immediate sweep",{im[11:0],5'd6,3'd0,5'd5,7'h13},24'h102448);
            check("SLTI immediate sweep",{im[11:0],5'd6,3'd2,5'd5,7'h13},24'h182448);
            check("SLTIU immediate sweep",{im[11:0],5'd6,3'd3,5'd5,7'h13},24'h192448);
            check("XORI immediate sweep",{im[11:0],5'd6,3'd4,5'd5,7'h13},24'h142448);
            check("ORI immediate sweep",{im[11:0],5'd6,3'd6,5'd5,7'h13},24'h132448);
            check("ANDI immediate sweep",{im[11:0],5'd6,3'd7,5'd5,7'h13},24'h122448);
        end

        // All register numbers; independent numeric expected field checks.
        for (r=0; r<32; r++) begin
            expected_rs2=5'd31-r[4:0];
            word_value={7'b0,expected_rs2,r[4:0],3'b000,r[4:0],7'h33};
            check("register field sweep",word_value,24'h100048);
            if ((rs1_addr !== r[4:0]) || (rs2_addr !== expected_rs2) || (rd_addr !== r[4:0]))
                $fatal(1,"FAIL independent register field check r=%0d",r);
        end

        // Visit every funct3 of memory, branch, JALR and MISC-MEM opcodes.
        for (f3=0; f3<8; f3++) begin
            golden=SAFE;
            case (f3)
                0: golden=24'h20240a;
                1: golden=24'h20242a;
                2: golden=24'h20244a;
                4: golden=24'h20241a;
                5: golden=24'h20243a;
                default: begin end
            endcase
            check("load funct3 sweep",{12'hffc,5'd6,f3[2:0],5'd5,7'h03},golden);
            golden=SAFE;
            case (f3)
                0: golden=24'h304400;
                1: golden=24'h304420;
                2: golden=24'h304440;
                default: begin end
            endcase
            check("store funct3 sweep",{12'hffc,5'd6,f3[2:0],5'd5,7'h23},golden);
            golden=SAFE;
            case (f3)
                0: golden=24'h406cc0;
                1: golden=24'h406d40;
                4: golden=24'h406dc0;
                5: golden=24'h406e40;
                6: golden=24'h406ec0;
                7: golden=24'h406f40;
                default: begin end
            endcase
            check("branch funct3 sweep",{12'hffc,5'd6,f3[2:0],5'd5,7'h63},golden);
            golden=SAFE;
            case (f3)
                0: golden=24'h60244c;
                default: begin end
            endcase
            check("jalr funct3 sweep",{12'hffc,5'd6,f3[2:0],5'd5,7'h67},golden);
            golden=SAFE;
            case (f3)
                0: golden=24'h701440;
                default: begin end
            endcase
            check("fence funct3 sweep",{12'hffc,5'd6,f3[2:0],5'd5,7'h0f},golden);
        end

        // FENCE ignores all reserved fm values and nonzero rs1/rd.
        for (fm=0; fm<16; fm++) begin
            check("FENCE reserved fields",{fm[3:0],8'hff,5'd31,3'b000,5'd31,7'h0f},24'h701440);
        end

        verbose=1;
        check("all zeros",32'h00000000,SAFE);
        check("all ones",32'hffffffff,SAFE);
        check("MUL unsupported",32'h027302b3,SAFE);
        check("FENCE.I unsupported",32'h0000100f,SAFE);
        check("CSRRW unsupported",32'h300312f3,SAFE);
        check("CSRRS unsupported",32'h300322f3,SAFE);
        check("MRET unsupported",32'h30200073,SAFE);
        check("WFI unsupported",32'h10500073,SAFE);
        check("ECALL nonzero rd",32'h000000f3,SAFE);
        check("ECALL nonzero rs1",32'h00080073,SAFE);
        check("EBREAK nonzero rd",32'h001000f3,SAFE);
        check("EBREAK nonzero rs1",32'h00108073,SAFE);
        check("unknown SYSTEM immediate",32'h00200073,SAFE);
        check("RV64 OP-IMM-32",32'h0003029b,SAFE);
        check("RV64 OP-32",32'h007302bb,SAFE);
        check("compressed encoding",32'h00000001,SAFE);
        check("custom not yet implemented",32'h0073028b,SAFE);
        check("canonical NOP",32'h00000013,24'h102448);
        check("load to x0 retains load",32'h00032003,24'h20244a);
        check("jump to x0 retains jump",32'h0040006f,24'h50ac4c);
        // Interleave invalid and valid instructions to expose stale controls.
        check("invalid after jump",32'hffffffff,SAFE);
        check("valid ADD after invalid",32'h007302b3,24'h100048);
        check("invalid after ADD",32'h027302b3,SAFE);
        $display("ALL %0d DECODER CHECKS PASSED",test_count);
        $finish;
    end
    initial begin
        #100000;
        $fatal(1,"TIMEOUT tb_decoder");
    end
endmodule
