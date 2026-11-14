from pathlib import Path
import json
root=Path(__file__).resolve().parent
MASK=0xffffffff
def signed(v):return v-0x100000000 if v&0x80000000 else v
def iword(imm,rs,rd,op=0x13,f3=0):return ((imm&4095)<<20)|(rs<<15)|(f3<<12)|(rd<<7)|op
def bword(off,a,b,f3):
    v=off&8191
    return ((v>>12)<<31)|(((v>>5)&63)<<25)|(b<<20)|(a<<15)|(f3<<12)|(((v>>1)&15)<<8)|(((v>>11)&1)<<7)|0x63
def jword(off,rd):
    v=off&0x1fffff
    return ((v>>20)<<31)|(((v>>1)&1023)<<21)|(((v>>11)&1)<<20)|(((v>>12)&255)<<12)|(rd<<7)|0x6f
preds={'beq':lambda a,b:a==b,'bne':lambda a,b:a!=b,'blt':lambda a,b:signed(a)<signed(b),
       'bge':lambda a,b:signed(a)>=signed(b),'bltu':lambda a,b:a<b,'bgeu':lambda a,b:a>=b}
f3s={'beq':0,'bne':1,'blt':4,'bge':5,'bltu':6,'bgeu':7}
class Program:
    def __init__(self):self.ops=[];self.labels={}
    def label(self,name):self.labels[name]=len(self.ops)*4
    def emit(self,op,*args):self.ops.append((op,*args))
    def li(self,rd,v):
        v&=MASK
        low=v&4095; low=low-4096 if low&2048 else low
        high=((v-low)>>12)&0xfffff
        if high:self.emit('lui',rd,high); self.emit('addi',rd,rd,low)
        else:self.emit('addi',rd,0,low)
    def offset(self,t,pc):return self.labels[t]-pc if isinstance(t,str) else t
    def encode(self,ins,pc):
        op,*a=ins
        if op=='addi':return iword(a[2],a[1],a[0])
        if op=='lui':return (a[1]<<12)|(a[0]<<7)|0x37
        if op=='add':return (a[2]<<20)|(a[1]<<15)|(a[0]<<7)|0x33
        if op in preds:return bword(self.offset(a[2],pc),a[0],a[1],f3s[op])
        if op=='jal':return jword(self.offset(a[1],pc),a[0])
        if op=='jalr':return iword(a[2],a[1],a[0],0x67)
        if op=='ebreak':return 0x00100073
        if op=='ecall':return 0x00000073
        if op=='raw':return a[0]
        raise ValueError(ins)
    def model(self,error_index=-1):
        regs=[0]*32;pc=0;trace=[];words=[self.encode(ins,k*4) for k,ins in enumerate(self.ops)]
        for step in range(200):
            if pc//4>=len(words) or pc//4==error_index:return words,trace,regs,[3,pc,pc]
            ins=self.ops[pc//4];op,*a=ins;rd=0;value=0;nxt=(pc+4)&MASK
            if op=='ebreak':return words,trace,regs,[9,pc,0]
            if op=='ecall':return words,trace,regs,[8,pc,0]
            if op=='raw':return words,trace,regs,[1,pc,0]
            if op=='addi':rd=a[0];value=(regs[a[1]]+a[2])&MASK
            elif op=='lui':rd=a[0];value=a[1]<<12
            elif op=='add':rd=a[0];value=(regs[a[1]]+regs[a[2]])&MASK
            elif op in preds:
                if preds[op](regs[a[0]],regs[a[1]]):nxt=(pc+self.offset(a[2],pc))&MASK
                if nxt&3:return words,trace,regs,[2,pc,nxt]
            elif op=='jal':
                rd=a[0];value=(pc+4)&MASK;nxt=(pc+self.offset(a[1],pc))&MASK
                if nxt&3:return words,trace,regs,[2,pc,nxt]
            elif op=='jalr':
                nxt=((regs[a[1]]+a[2])&MASK)&0xfffffffe;rd=a[0];value=(pc+4)&MASK
                if nxt&3:return words,trace,regs,[2,pc,nxt]
            else:raise ValueError(ins)
            trace.append([pc,words[pc//4],rd if rd else 0,value if rd else 0,nxt])
            if rd:regs[rd]=value
            regs[0]=0;pc=nxt
        raise RuntimeError('reference program loops forever')
cases=[]
def save(name,p,error_index=-1):
    words,trace,regs,stop=p.model(error_index)
    cases.append(dict(name=name,words=words,trace=trace,regs=regs,stop=stop,error_index=error_index,
                      assembly=[' '.join(map(str,ins)) for ins in p.ops]))

# Existing integer test uses manually fixed writeback values, independent of this model.
old=json.loads((root/'reference_inputs/program_spec.json').read_text())
regs=[0]*32;trace=[]
for idx,(asm,word,rd,value) in enumerate(old):
    trace.append([idx*4,word,rd,value,idx*4+4])
    if rd:regs[rd]=value
cases.append(dict(name='integer instruction regression',words=[r[1] for r in old]+[0x00100073],trace=trace,
                  regs=regs,stop=[9,len(old)*4,0],error_index=-1,assembly=[r[0] for r in old]+['ebreak']))

for op in preds:
    for a,b in [(MASK,1),(1,MASK),(7,7),(0x80000000,0x7fffffff)]:
        p=Program();p.li(1,a);p.li(2,b);p.emit(op,1,2,'target');p.emit('addi',31,0,99)
        p.label('target');p.emit('addi',3,0,5);p.emit('ebreak')
        save(f'{op} a={a:08x} b={b:08x}',p)
    # Equal and unequal values exercise both outcomes, with signed-specific order.
    true_pair={'beq':(1,1),'bne':(1,2),'blt':(-1,1),'bge':(1,-1),'bltu':(1,2),'bgeu':(2,1)}[op]
    false_pair={'beq':(1,2),'bne':(1,1),'blt':(1,-1),'bge':(-1,1),'bltu':(2,1),'bgeu':(1,2)}[op]
    for outcome,pair in [('taken',true_pair),('not taken',false_pair)]:
        p=Program();p.li(1,pair[0]);p.li(2,pair[1]);p.emit(op,1,2,2);p.emit('addi',3,0,7);p.emit('ebreak')
        save(f'{op} {outcome} target misaligned',p)

p=Program();p.li(1,5);p.li(2,0);p.li(3,0);p.label('loop');p.emit('addi',2,2,1);p.emit('add',3,3,2)
p.emit('blt',2,1,'loop');p.emit('jal',1,'function');p.emit('jal',0,'done')
p.label('function');p.emit('addi',3,3,10);p.emit('jalr',0,1,0);p.label('done');p.emit('ebreak')
save('backward loop and function return',p);loop_id=len(cases)-1
assert cases[-1]['regs'][3]==25
p=Program();p.emit('jal',1,'outer');p.emit('jal',0,'done');p.label('outer');p.emit('addi',5,1,0)
p.emit('jal',1,'inner');p.emit('addi',10,10,2);p.emit('jalr',0,5,0)
p.label('inner');p.emit('addi',10,10,3);p.emit('jalr',0,1,0);p.label('done');p.emit('ebreak')
save('nested calls preserving outer return register',p);assert cases[-1]['regs'][10]==5

for name,base,off,rd in [('JALR clears odd bit zero',17,0,1),('JALR negative offset',24,-8,1),
                          ('JALR rd equals rs1',16,0,5),('JALR rd x0',16,0,0),
                          ('JALR offset bit zero',16,1,1),('JALR clears bit0 but bit1 remains',19,0,1),
                          ('JALR high aligned address fetch fails',0xfffffffd,0,1),
                          ('JALR maximum positive immediate',1,2047,1),
                          ('JALR minimum negative immediate',2064,-2048,1)]:
    p=Program();p.li(5,base);p.emit('jalr',rd,5,off)
    while len(p.ops)*4<16:p.emit('addi',31,0,99)
    p.emit('addi',6,0,7);p.emit('ebreak');save(name,p)
for name,off,rd in [('JAL misaligned keeps link',2,1),('JAL x0 skips instruction',8,0),('JAL high target fetch fails',-4,1)]:
    p=Program();p.emit('addi',1,0,77);p.emit('jal',rd,off);p.emit('addi',31,0,99);p.emit('ebreak')
    # For high target the jump must be at address zero to underflow.
    if off==-4:p=Program();p.emit('jal',rd,-4)
    save(name,p)
p=Program();p.emit('jal',0,'start');p.label('back');p.emit('addi',10,0,9);p.emit('jal',0,'done')
p.label('start');p.emit('jal',1,'back');p.label('done');p.emit('ebreak');save('JAL negative offset within program',p)
for off in [4092,4094,-4096]:
    p=Program();p.emit('beq',0,0,off);save(f'branch displacement boundary {off}',p)
for off in [1048572,1048574,-1048576]:
    p=Program();p.emit('jal',1,off);save(f'JAL displacement boundary {off}',p)
for name,word in [('load remains unsupported',0x00002083),('store remains unsupported',0x00002023),
                  ('MUL illegal',0x027302b3),('reserved branch funct3 illegal',0x00002063),
                  ('JALR nonzero funct3 illegal',0x00001067)]:
    p=Program();p.emit('addi',1,0,5);p.emit('raw',word);save(name,p)
p=Program();p.emit('jal',1,8);p.emit('addi',31,0,99);p.emit('ebreak');save('jump target fetch error preserves link',p,2)
p=Program();p.emit('addi',1,0,5);p.emit('ecall');save('ECALL regression',p)
p=Program();p.emit('addi',1,0,5);p.emit('ebreak');save('sequential fetch error regression',p,1)

(root/'cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
lines=['case(case_id)']
for idx,c in enumerate(cases):
    lines.append(f'{idx}: begin case_name="{c["name"]}"; program_len={len(c["words"])}; expected_commits={len(c["trace"])}; error_index={c["error_index"]};')
    cause,pc,addr=c['stop'];lines.append(f"expected_cause=halt_cause_t'({cause}); expected_fault_pc=32'h{pc:08x}; expected_fault_addr=32'h{addr:08x};")
    for k,w in enumerate(c['words']):lines.append(f"program_words[{k}]=32'h{w:08x};")
    for k,(pc,w,rd,v,nxt) in enumerate(c['trace']):
        lines.append(f"expected_pc[{k}]=32'h{pc:08x}; expected_inst[{k}]=32'h{w:08x}; expected_rd[{k}]=5'd{rd}; expected_value[{k}]=32'h{v:08x}; expected_next[{k}]=32'h{nxt:08x};")
    for k,v in enumerate(c['regs']):lines.append(f"golden_regs[{k}]=32'h{v:08x};")
    lines.append('end')
lines+=['default: $fatal(1,"bad case id");','endcase']
(root/'verify/cases_init.svh').write_text('\n'.join(lines)+'\n',encoding='utf-8')
for idx in [0,loop_id,loop_id+1]:
    (root/f'verify/program_{idx}.mem').write_text('\n'.join(f'{w:08x}' for w in cases[idx]['words'])+'\n')
# Reuse the validated single-transaction memory model; new golden trace handles nonsequential PC.
oldtb=(root/'reference_inputs/tb_integer_template.txt').read_text()
tb=oldtb[:oldtb.index('    task automatic short_fault')]
tb=tb.replace('module tb_fault_v_cpu;','module tb_branch_cpu;')
tb=tb.replace('expected_value[0:63],expected_regs[0:31]','expected_value[0:255],expected_regs[0:31],golden_regs[0:31]')
tb=tb.replace('expected_rd[0:63]','expected_rd[0:255]')
tb=tb.replace('logic busy,stalled;', 'logic busy,stalled;\n    logic [31:0] expected_pc[0:255],expected_inst[0:255],expected_next[0:255],previous_next;\n    string case_name;\n    halt_cause_t expected_cause;\n    logic [31:0] expected_fault_pc,expected_fault_addr;\n    integer case_id,delay_mode;')
start=tb.index('    task automatic load_long_program;');end=tb.index('    task automatic reset_core;')
tb=tb[:start]+'''    task automatic load_case(input integer case_id);
        for (integer k=0;k<64;k=k+1) program_words[k]=0;
        `include "cases_init.svh"
    endtask
'''+tb[end:]
tb=tb.replace('if (!previous_commit) must(pc==previous_pc,"PC held until commit");',
'''if (!previous_commit) must(pc==previous_pc,"PC held until commit");
            else must(pc===previous_next,"committed next PC");''')
tb=tb.replace('retire_pc==retired*4,"sequential instruction PC"','retire_pc===expected_pc[retired],"instruction PC"')
tb=tb.replace('program_words[retired],"executed requested instruction"','expected_inst[retired],"executed requested instruction"')
tb=tb.replace('retired=retired+1;', 'previous_next=expected_next[retired];\n                retired=retired+1;')
tb=tb.replace('must(dut.u_regfile.regs[r]===expected_regs[r],"final register file matches golden trace");',
'''begin
                must(dut.u_regfile.regs[r]===golden_regs[r],"final register file matches independent model");
                must(expected_regs[r]===golden_regs[r],"commit trace matches independent final state");
            end''')
tb+='''    initial begin
        rst=1; mode=0; error_index=-1;
        dmem_req_ready=0; dmem_rsp_valid=0; dmem_rsp_err=0; dmem_rsp_data=0;
        for (case_id=0;case_id<CASE_COUNT;case_id=case_id+1) begin
            for (delay_mode=0;delay_mode<2;delay_mode=delay_mode+1) begin
                @(negedge clk); rst=1; mode=delay_mode*2; load_case(case_id);
                tick; @(negedge clk); rst=0;
                await_halt(case_name,expected_cause,expected_fault_pc,expected_fault_addr);
            end
        end
        // Cancel execution immediately before a branch or jump commit, then restart.
        for (integer k=0;k<2;k=k+1) begin
            @(negedge clk); rst=1; mode=2; load_case(LOOP_ID);
            tick; @(negedge clk); rst=0;
            cycles=0;
            while (state!=((k==0)?ST_BR_COMMIT:ST_JUMP_COMMIT)) begin
                tick; cycles=cycles+1;
                if (cycles>3000) $fatal(1,"reset setup timeout");
            end
            reset_core;
            await_halt("reset before control-flow commit then restart",expected_cause,expected_fault_pc,expected_fault_addr);
        end
        $display("ALL %0d BRANCH CPU SCENARIOS PASSED",scenarios);
        $finish;
    end
    initial begin #1000000; $fatal(1,"GLOBAL TIMEOUT tb_branch_cpu"); end
endmodule
'''.replace('CASE_COUNT',str(len(cases))).replace('LOOP_ID',str(loop_id))
(root/'verify/tb_branch_cpu.sv').write_text(tb,encoding='utf-8')
print(f'{len(cases)} programs, {len(cases)*2+2} scenarios, loop id {loop_id}')
