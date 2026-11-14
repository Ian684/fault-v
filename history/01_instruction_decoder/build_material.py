from pathlib import Path

ROOT=Path(__file__).resolve().parent
(ROOT/'verify').mkdir(exist_ok=True)

# Explicit test specification: mnemonic, instruction, operation and control fields.
# This table does not call or inspect the DUT.
ops={'ADD':0,'SUB':1,'AND':2,'OR':3,'XOR':4,'SLL':5,'SRL':6,'SRA':7,'SLT':8,'SLTU':9}
rows=[]
def row(n,i,cl,op=0,im=0,a=2,b=1,br=0,ms=2,u=0,rw=0,wb=0):
    rows.append((n,i,cl,op,im,a,b,br,ms,u,rw,wb))
for n,i in [('ADD',0x007302b3),('SUB',0x407302b3),('SLL',0x007312b3),('SLT',0x007322b3),('SLTU',0x007332b3),('XOR',0x007342b3),('SRL',0x007352b3),('SRA',0x407352b3),('OR',0x007362b3),('AND',0x007372b3)]:
    row(n,i,1,ops[n],a=0,b=0,rw=1)
for n,i,op in [('ADDI',0xffc30293,0),('SLTI',0xffc32293,8),('SLTIU',0xffc33293,9),('XORI',0xffc34293,4),('ORI',0xffc36293,3),('ANDI',0xffc37293,2),('SLLI',0x01f31293,5),('SRLI',0x01f35293,6),('SRAI',0x41f35293,7)]:
    row(n,i,1,op,1,0,rw=1)
row('LUI',0x123452b7,1,im=4,rw=1)
row('AUIPC',0x12345297,1,im=4,a=1,rw=1)
for n,i,br in [('BEQ',0xfe730ee3,1),('BNE',0xfe731ee3,2),('BLT',0xfe734ee3,3),('BGE',0xfe735ee3,4),('BLTU',0xfe736ee3,5),('BGEU',0xfe737ee3,6)]:
    row(n,i,4,im=3,a=1,br=br)
row('JAL',0xffdff2ef,5,im=5,a=1,rw=1,wb=2)
row('JALR',0xffc302e7,6,im=1,a=0,rw=1,wb=2)
for n,i,ms,u in [('LB',0xffc30283,0,0),('LH',0xffc31283,1,0),('LW',0xffc32283,2,0),('LBU',0xffc34283,0,1),('LHU',0xffc35283,1,1)]:
    row(n,i,2,im=1,a=0,ms=ms,u=u,rw=1,wb=1)
for n,i,ms in [('SB',0xfe730e23,0),('SH',0xfe731e23,1),('SW',0xfe732e23,2)]:
    row(n,i,3,im=2,a=0,ms=ms)
row('FENCE',0x0ff0000f,7)
row('ECALL',0x00000073,8)
row('EBREAK',0x00100073,9)
assert len(rows)==40

decl='''    logic [31:0] instruction;
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
'''
def ctrl(cl=0,op=0,im=0,a=2,b=1,br=0,ms=2,u=0,rw=0,wb=0,illegal=1):
    vals=[(cl,4),(op,4),(im,3),(a,2),(b,1),(br,3),(ms,2),(u,1),(rw,1),(wb,2),(illegal,1)]
    v=0
    for x,w in vals: v=(v<<w)|x
    return v
bad=ctrl()
calls='\n'.join(f'        check("{n}",32\'h{i:08x},24\'h{ctrl(*cs,illegal=0):06x});' for n,i,*cs in rows)
tb='''module tb_decoder;
    timeunit 1ns;
    timeprecision 1ps;
    import fault_v_pkg::*;
'''+decl+f'''
    int test_count=0;
    bit verbose=1;
    localparam logic [23:0] SAFE=24'h{bad:06x};
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
        observed={{instr_class,alu_op,imm_sel,alu_src_a,alu_src_b,
                  branch_op,mem_size,load_unsigned,rd_write,wb_sel,illegal}};
        if (observed !== expected)
            $fatal(1,"FAIL %s inst=%h controls=%h expected=%h",label_text,inst,observed,expected);
        if ((rs1_addr !== inst[19:15]) || (rs2_addr !== inst[24:20]) || (rd_addr !== inst[11:7]))
            $fatal(1,"FAIL %s register fields rs1=%0d rs2=%0d rd=%0d",label_text,rs1_addr,rs2_addr,rd_addr);
        test_count++;
        if (verbose) $display("PASS %0d: %s inst=%h controls=%h",test_count,label_text,inst,observed);
    endtask

    initial begin
{calls}
        verbose=0;

        // All 128 funct7 values x all eight funct3 values for opcode 0x33.
        for (f7=0; f7<128; f7++) begin
            for (f3=0; f3<8; f3++) begin
                golden=SAFE;
                case ({{f7[6:0],f3[2:0]}})
'''
for n,i,*cs in rows[:10]:
    tb+=f"                    10'h{(((i>>25)&127)<<3)|((i>>12)&7):03x}: golden=24'h{ctrl(*cs,illegal=0):06x};\n"
tb+='''                    default: begin end
                endcase
                word_value={f7[6:0],5'd7,5'd6,f3[2:0],5'd5,7'h33};
                check("R encoding sweep",word_value,golden);
            end
        end

        // RV32 immediate shifts: all upper seven bits and all 32 shift amounts.
        for (f7=0; f7<128; f7++) begin
            for (sh=0; sh<32; sh++) begin
'''
slli=ctrl(1,5,1,0,rw=1,illegal=0);srli=ctrl(1,6,1,0,rw=1,illegal=0);srai=ctrl(1,7,1,0,rw=1,illegal=0)
tb+=f'''                golden=SAFE;
                if (f7==0) golden=24'h{slli:06x};
                check("SLLI encoding sweep",{{f7[6:0],sh[4:0],5'd6,3'b001,5'd5,7'h13}},golden);
                golden=SAFE;
                if (f7==0) golden=24'h{srli:06x};
                else if (f7==32) golden=24'h{srai:06x};
                check("SRLI/SRAI encoding sweep",{{f7[6:0],sh[4:0],5'd6,3'b101,5'd5,7'h13}},golden);
            end
        end

        // No funct7 restriction on the six non-shift I-type operations.
        for (im=0; im<4096; im++) begin
'''
for n,i,*cs in rows[10:16]:
    tb+=f"            check(\"{n} immediate sweep\",{{im[11:0],5'd6,3'd{(i>>12)&7},5'd5,7'h13}},24'h{ctrl(*cs,illegal=0):06x});\n"
tb+='''        end

        // All register numbers; independent numeric expected field checks.
        for (r=0; r<32; r++) begin
            expected_rs2=5'd31-r[4:0];
            word_value={7'b0,expected_rs2,r[4:0],3'b000,r[4:0],7'h33};
'''+f'''            check("register field sweep",word_value,24'h{ctrl(1,0,0,0,0,rw=1,illegal=0):06x});
'''+'''            if ((rs1_addr !== r[4:0]) || (rs2_addr !== expected_rs2) || (rd_addr !== r[4:0]))
                $fatal(1,"FAIL independent register field check r=%0d",r);
        end

        // Visit every funct3 of memory, branch, JALR and MISC-MEM opcodes.
        for (f3=0; f3<8; f3++) begin
'''
for opcode,cl,select in [(3,2,'load'),(0x23,3,'store'),(0x63,4,'branch'),(0x67,6,'jalr'),(0xf,7,'fence')]:
    tb+='            golden=SAFE;\n            case (f3)\n'
    for n,i,*cs in rows:
        if i&127==opcode:
            tb+=f"                {(i>>12)&7}: golden=24'h{ctrl(*cs,illegal=0):06x};\n"
    tb+='                default: begin end\n            endcase\n'
    # Offset/fm bits freely set, exact system not used here
    tb+=f"            check(\"{select} funct3 sweep\",{{12'hffc,5'd6,f3[2:0],5'd5,7'h{opcode:02x}}},golden);\n"
tb+='''        end

        // FENCE ignores all reserved fm values and nonzero rs1/rd.
        for (fm=0; fm<16; fm++) begin
'''+f'''            check("FENCE reserved fields",{{fm[3:0],8'hff,5'd31,3'b000,5'd31,7'h0f}},24'h{ctrl(7,illegal=0):06x});
'''+'''        end

        verbose=1;
'''
negative=[('all zeros',0),('all ones',0xffffffff),('MUL unsupported',0x027302b3),('FENCE.I unsupported',0x100f),('CSRRW unsupported',0x300312f3),('CSRRS unsupported',0x300322f3),('MRET unsupported',0x30200073),('WFI unsupported',0x10500073),('ECALL nonzero rd',0xf3),('ECALL nonzero rs1',0x80073),('EBREAK nonzero rd',0x1000f3),('EBREAK nonzero rs1',0x108073),('unknown SYSTEM immediate',0x200073),('RV64 OP-IMM-32',0x3029b),('RV64 OP-32',0x7302bb),('compressed encoding',1),('custom not yet implemented',0x73028b)]
for n,i in negative:tb+=f'        check("{n}",32\'h{i:08x},SAFE);\n'
tb+=f'''        check("canonical NOP",32'h00000013,24'h{ctrl(1,0,1,0,rw=1,illegal=0):06x});
        check("load to x0 retains load",32'h00032003,24'h{ctrl(2,im=1,a=0,rw=1,wb=1,illegal=0):06x});
        check("jump to x0 retains jump",32'h0040006f,24'h{ctrl(5,im=5,a=1,rw=1,wb=2,illegal=0):06x});
        // Interleave invalid and valid instructions to expose stale controls.
        check("invalid after jump",32'hffffffff,SAFE);
        check("valid ADD after invalid",32'h007302b3,24'h{ctrl(1,0,0,0,0,rw=1,illegal=0):06x});
        check("invalid after ADD",32'h027302b3,SAFE);
        $display("ALL %0d DECODER CHECKS PASSED",test_count);
        $finish;
    end
    initial begin
        #100000;
        $fatal(1,"TIMEOUT tb_decoder");
    end
endmodule
'''
(ROOT/'verify/tb_decoder.sv').write_text(tb,encoding='utf-8')

integration=[
 ('ADD',0x007302b3,5,3,0x100,0,8,8,8),
 ('SUB negative',0x407302b3,3,5,0x100,0,0xfffffffe,0xfffffffe,0xfffffffe),
 ('SLL mask',0x007312b3,1,32,0x100,0,1,1,1),
 ('SLT signed',0x007322b3,0xffffffff,1,0x100,0,1,1,1),
 ('SLTU unsigned',0x007332b3,0xffffffff,1,0x100,0,0,0,0),
 ('XOR',0x007342b3,10,12,0x100,0,6,6,6),
 ('SRL',0x007352b3,0x80000000,1,0x100,0,0x40000000,0x40000000,0x40000000),
 ('SRA',0x407352b3,0x80000000,1,0x100,0,0xc0000000,0xc0000000,0xc0000000),
 ('OR',0x007362b3,10,12,0x100,0,14,14,14),
 ('AND',0x007372b3,10,12,0x100,0,8,8,8),
 ('ADDI negative',0xffc30293,10,0xdeadbeef,0x100,0xfffffffc,6,6,6),
 ('SLTI signed',0xffc32293,0xfffffff8,0,0x100,0xfffffffc,1,1,1),
 ('SLTIU sign-extended immediate',0xffc33293,0,0,0x100,0xfffffffc,1,1,1),
 ('XORI negative',0xffc34293,0x12345678,0,0x100,0xfffffffc,0xedcba984,0xedcba984,0xedcba984),
 ('ORI negative',0xffc36293,0x12345678,0,0x100,0xfffffffc,0xfffffffc,0xfffffffc,0xfffffffc),
 ('ANDI negative',0xffc37293,0x1234567b,0,0x100,0xfffffffc,0x12345678,0x12345678,0x12345678),
 ('SLLI 31',0x01f31293,1,0,0x100,31,0x80000000,0x80000000,0x80000000),
 ('SRLI 31',0x01f35293,0x80000000,0,0x100,31,1,1,1),
 ('SRAI 31',0x41f35293,0x80000000,0,0x100,0x41f,0xffffffff,0xffffffff,0xffffffff),
 ('LUI',0x123452b7,0xdeadbeef,0,0x100,0x12345000,0x12345000,0x12345000,0x12345000),
 ('AUIPC',0x12345297,0xdeadbeef,0,0x100,0x12345000,0x12345100,0x12345100,0x12345100),
 ('Branch backward target',0xfe730ee3,0xdeadbeef,0,0x100,0xfffffffc,0xfc,0xfc,0),
 ('JAL target and link',0xffdff2ef,0,0,0x100,0xfffffffc,0xfc,0xfc,0x104),
 ('JALR clear bit zero',0x000302e7,0x101,0,0x100,0,0x101,0x100,0x104),
 ('JALR negative offset',0xffc302e7,0x200,0,0x100,0xfffffffc,0x1fc,0x1fc,0x104),
 ('LW effective address',0xffc32283,0x10000008,0,0x100,0xfffffffc,0x10000004,0x10000004,0),
 ('SW effective address',0xfe732e23,0x10000008,0x12345678,0x100,0xfffffffc,0x10000004,0x10000004,0),
 ('FENCE safe controls',0x0ff0000f,0xdeadbeef,0xffffffff,0x100,0,0,0,0),
 ('ECALL safe controls',0x73,0xdeadbeef,0xffffffff,0x100,0,0,0,0),
 ('EBREAK safe controls',0x100073,0xdeadbeef,0xffffffff,0x100,0,0,0,0),
 ('Illegal safe controls',0xffffffff,0xdeadbeef,0xffffffff,0x100,0,0,0,0),
 ('ADDI after illegal',0xffc30293,10,0,0x100,0xfffffffc,6,6,6),
 ('ADDI overflow wraps',0x00130293,0xffffffff,0,0x100,1,0,0,0),
]
itb='''module tb_decode_path;
    timeunit 1ns;
    timeprecision 1ps;
    import fault_v_pkg::*;
'''+decl+'''
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
'''
for n,*v in integration:
    itb+='        check("'+n+'",'+','.join(f"32'h{x:08x}" for x in v)+');\n'
itb+='''        $display("ALL %0d DECODE PATH CASES PASSED",test_count);
        $finish;
    end
    initial begin
        #10000;
        $fatal(1,"TIMEOUT tb_decode_path");
    end
endmodule
'''
(ROOT/'verify/tb_decode_path.sv').write_text(itb,encoding='utf-8')

import json
(ROOT/'test_spec.json').write_text(json.dumps({'decoder':rows,'integration':integration},indent=2),encoding='utf-8')
print('Generated 40 instruction vectors, exhaustive control sweeps and',len(integration),'integration vectors.')
