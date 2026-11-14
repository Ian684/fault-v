from pathlib import Path
import json
from reference_model import Program, MASK, signed, preds, iword
root=Path(__file__).resolve().parent
BASE=0x10000000; MMIO=0x20000000; N=256
sizes={'lb':1,'lbu':1,'lh':2,'lhu':2,'lw':4,'sb':1,'sh':2,'sw':4}
f3s={'lb':0,'lbu':4,'lh':1,'lhu':5,'lw':2,'sb':0,'sh':1,'sw':2}
initial=[(k*73+128)&255 for k in range(N)]+[0]*4
def mapped(a):return BASE<=a<BASE+N or MMIO<=a<MMIO+4
def idx(a):return a-BASE if BASE<=a<BASE+N else N+a-MMIO
class MemoryProgram(Program):
    def run(self,fail_addr=-1,fail_write=-1):
        regs=[0]*32;mem=initial.copy();pc=0;trace=[];tx=[]
        words=[self.encode(ins,k*4) for k,ins in enumerate(self.ops)]
        for step in range(200):
            if pc//4>=len(words):return words,trace,regs,mem,tx,[3,pc,pc]
            ins=self.ops[pc//4];op,*a=ins;rd=0;value=0;nxt=(pc+4)&MASK
            if op=='ebreak':return words,trace,regs,mem,tx,[9,pc,0]
            if op=='ecall':return words,trace,regs,mem,tx,[8,pc,0]
            if op=='raw':return words,trace,regs,mem,tx,[1,pc,0]
            if op=='addi':rd=a[0];value=(regs[a[1]]+a[2])&MASK
            elif op=='lui':rd=a[0];value=a[1]<<12
            elif op=='add':rd=a[0];value=(regs[a[1]]+regs[a[2]])&MASK
            elif op in preds:
                if preds[op](regs[a[0]],regs[a[1]]):nxt=(pc+self.offset(a[2],pc))&MASK
                if nxt&3:return words,trace,regs,mem,tx,[2,pc,nxt]
            elif op=='jal':
                rd=a[0];value=pc+4;nxt=(pc+self.offset(a[1],pc))&MASK
                if nxt&3:return words,trace,regs,mem,tx,[2,pc,nxt]
            elif op=='jalr':
                nxt=((regs[a[1]]+a[2])&MASK)&0xfffffffe;rd=a[0];value=pc+4
                if nxt&3:return words,trace,regs,mem,tx,[2,pc,nxt]
            elif op=='fence':pass
            elif op in sizes:
                reg,base,off=a;size=sizes[op];write=int(op.startswith('s'));addr=(regs[base]+off)&MASK
                if addr%size:return words,trace,regs,mem,tx,[5 if write else 4,pc,addr]
                if addr>>12==0x20000 and size!=4:return words,trace,regs,mem,tx,[7 if write else 6,pc,addr]
                aligned=addr&0xfffffffc;lane=addr%4
                error=not all(mapped(aligned+k) for k in range(4)) or (aligned==fail_addr and (fail_write<0 or write==fail_write))
                raw=sum(mem[idx(aligned+k)]<<(k*8) for k in range(4)) if not error else 0
                # Model byte-addressed storage. Bus lane fields are computed separately.
                mask=((1<<size)-1)<<lane if write else 0
                wd=((regs[reg]&((1<<(8*size))-1))<<(8*lane)) if write else 0
                tx.append([aligned,write,wd,mask,raw,int(error)])
                if error:return words,trace,regs,mem,tx,[7 if write else 6,pc,addr]
                if write:
                    for k in range(size):mem[idx(addr+k)]=(regs[reg]>>(8*k))&255
                else:
                    rd=reg;value=sum(mem[idx(addr+k)]<<(8*k) for k in range(size))
                    if op in ['lb','lh'] and value&(1<<(size*8-1)):value|=MASK^((1<<(8*size))-1)
            else:raise ValueError(ins)
            trace.append([pc,words[pc//4],rd if rd else 0,value if rd else 0,nxt])
            if rd:regs[rd]=value&MASK
            pc=nxt
        raise RuntimeError('program does not terminate')
    def encode(self,ins,pc):
        if ins[0]=='fence':return 0x0ff0000f
        op,*a=ins
        if op in sizes:
            reg,rs1,off=a
            if op.startswith('l'):return iword(off,rs1,reg,0x03,f3s[op])
            v=off&4095
            return ((v>>5)<<25)|(reg<<20)|(rs1<<15)|(f3s[op]<<12)|((v&31)<<7)|0x23
        return super().encode(ins,pc)
cases=[]
for c in json.loads((root/'reference_inputs/branch_cases.json').read_text()):
    if c['name'] in ['load remains unsupported','store remains unsupported']:continue
    c.update(mem=initial.copy(),tx=[],fail_addr=-1,fail_write=-1)
    cases.append(c)
def save(name,p,fail_addr=-1,fail_write=-1):
    w,t,r,m,tx,stop=p.run(fail_addr,fail_write)
    cases.append(dict(name=name,words=w,trace=t,regs=r,stop=stop,mem=m,tx=tx,error_index=-1,
                      fail_addr=fail_addr,fail_write=fail_write,assembly=[list(ins) for ins in p.ops]))
def base_program():
    p=MemoryProgram();p.li(1,BASE);return p
for op in ['lb','lbu','lh','lhu','lw']:
    for off in (range(4) if sizes[op]==1 else [0,2] if sizes[op]==2 else [0]):
        p=base_program();p.emit(op,2,1,off);p.emit('addi',3,2,1);p.emit('ebreak');save(f'{op} lane {off}',p)
for op in ['sb','sh','sw']:
    for off in (range(4) if sizes[op]==1 else [0,2] if sizes[op]==2 else [0]):
        p=base_program();p.li(2,0x89abcdef);p.emit(op,2,1,off);p.emit('lw',3,1,0);p.emit('ebreak');save(f'{op} lane {off} preserves other bytes',p)
p=base_program();p.emit('addi',1,1,8);p.li(2,0x8001ff80)
p.emit('sw',2,1,-8)
for op,off in [('lb',-8),('lbu',-8),('lb',-7),('lbu',-7),('lh',-6),('lhu',-6),('lw',-8)]:p.emit(op,3,1,off)
p.emit('ebreak');save('mixed signed loads and negative offsets',p)
p=base_program();p.li(2,0x76543210);p.emit('sw',2,1,0);p.emit('lw',2,1,0)
p.emit('addi',2,2,1);p.emit('sw',2,1,4);p.emit('lw',1,1,4);p.emit('ebreak');save('dependent loads stores and rd equals base',p)
p=base_program();p.emit('lw',0,1,0);p.emit('sb',0,1,1);p.emit('lw',2,1,0);p.emit('ebreak');save('load x0 still reads and store x0 writes zero',p)
p=base_program();p.emit('addi',2,1,0);p.emit('addi',3,0,4);p.emit('addi',4,0,1);p.emit('addi',5,0,0)
p.label('loop');p.emit('sw',4,2,0);p.emit('lw',6,2,0);p.emit('add',5,5,6);p.emit('addi',2,2,4)
p.emit('addi',4,4,1);p.emit('blt',4,3,'loop');p.emit('beq',4,3,'last');p.emit('ebreak')
p.label('last');p.emit('sw',4,2,0);p.emit('lw',6,2,0);p.emit('add',5,5,6);p.emit('fence');p.emit('ebreak')
save('memory loop sum with FENCE',p);loop_id=len(cases)-1;assert cases[-1]['regs'][5]==10
p=base_program();p.li(2,123);p.emit('jal',5,'func');p.emit('jal',0,'done');p.label('func')
p.emit('sw',2,1,0);p.emit('lw',3,1,0);p.emit('jalr',0,5,0);p.label('done');p.emit('ebreak');save('function with memory access',p)
for op in ['lh','lhu','lw','sh','sw']:
    for off in ([1,3] if sizes[op]==2 else [1,2,3]):
        p=base_program();p.li(2,77);p.emit(op,2,1,off);p.emit('ebreak');save(f'{op} rejects offset {off}',p)
for op in ['lb','lbu','lh','lhu','lw','sb','sh','sw']:
    p=base_program();p.li(2,77);p.emit(op,2,1,0);p.emit('ebreak');save(f'{op} injected response error',p,BASE,int(op.startswith('s')))
p=base_program();p.emit('lw',0,1,0);p.emit('ebreak');save('load x0 response error still halts',p,BASE,0)
for op in ['lb','lw','sb','sw']:
    p=base_program();p.emit(op,2,1,N);p.emit('ebreak');save(f'{op} unmapped address',p)
for op in ['lb','lbu','lh','lhu','sb','sh']:
    p=MemoryProgram();p.li(1,MMIO);p.emit(op,2,1,0);p.emit('ebreak');save(f'{op} rejects narrow MMIO without request',p)
p=MemoryProgram();p.li(1,MMIO);p.emit('lh',2,1,1);p.emit('ebreak');save('misalignment has priority over narrow MMIO',p)
p=MemoryProgram();p.li(1,MMIO);p.li(2,1);p.emit('sw',2,1,0);p.emit('lw',3,1,0);p.emit('fence');p.emit('ebreak');save('word MMIO status stub',p)
for word in [0x00003083,0x00006083,0x00003023]:
    p=base_program();p.emit('raw',word);save(f'illegal memory funct3 {word:08x}',p)

(root/'cases.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
lines=['for (integer m=0;m<260;m=m+1) golden_mem[m]=(m<256)?((m*73+128)&255):0;','case(case_id)']
for k,c in enumerate(cases):
    cause,pc,addr=c['stop'];lines.append(f'{k}: begin case_name="{c["name"]}"; program_len={len(c["words"])}; expected_commits={len(c["trace"])}; error_index={c["error_index"]}; expected_transactions={len(c["tx"])};')
    lines.append(f"expected_cause=halt_cause_t'({cause}); expected_fault_pc=32'h{pc:08x}; expected_fault_addr=32'h{addr:08x}; fail_addr=32'h{c['fail_addr']&MASK:08x}; fail_write={c['fail_write']};")
    for j,w in enumerate(c['words']):lines.append(f"program_words[{j}]=32'h{w:08x};")
    for j,(pc,w,rd,v,nxt) in enumerate(c['trace']):lines.append(f"expected_pc[{j}]=32'h{pc:08x}; expected_inst[{j}]=32'h{w:08x}; expected_rd[{j}]=5'd{rd}; expected_value[{j}]=32'h{v:08x}; expected_next[{j}]=32'h{nxt:08x};")
    for j,v in enumerate(c['regs']):lines.append(f"golden_regs[{j}]=32'h{v:08x};")
    for j,v in enumerate(c['mem']):
        if v!=initial[j]:lines.append(f"golden_mem[{j}]=8'h{v:02x};")
    for j,(a,wr,wd,mask,raw,err) in enumerate(c['tx']):lines.append(f"tx_addr[{j}]=32'h{a:08x}; tx_write[{j}]={wr}; tx_data[{j}]=32'h{wd:08x}; tx_mask[{j}]=4'h{mask:x}; tx_raw[{j}]=32'h{raw:08x}; tx_error[{j}]={err};")
    lines.append('end')
lines+=['default: $fatal(1,"bad memory case id");','endcase']
(root/'verify/cases_init.svh').write_text('\n'.join(lines)+'\n')
(root/'case_config.json').write_text(json.dumps(dict(programs=len(cases),scenarios=len(cases)*2+2,loop_id=loop_id)))
print(f'{len(cases)} programs, {len(cases)*2+2} scenarios; memory loop id {loop_id}')
