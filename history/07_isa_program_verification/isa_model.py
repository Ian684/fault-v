from pathlib import Path
import json
from assembler_support import Program, MASK, signed, preds, iword
root=Path(__file__).resolve().parent
BASE=0x10000000; MMIO=0x20000000; N=16384
sizes={'lb':1,'lbu':1,'lh':2,'lhu':2,'lw':4,'sb':1,'sh':2,'sw':4}
f3s={'lb':0,'lbu':4,'lh':1,'lhu':5,'lw':2,'sb':0,'sh':1,'sw':2}
initial=[0]*(N+4)
rr={'add':(0,0),'sub':(32,0),'sll':(0,1),'slt':(0,2),'sltu':(0,3),
    'xor':(0,4),'srl':(0,5),'sra':(32,5),'or':(0,6),'and':(0,7)}
ii={'addi':0,'slti':2,'sltiu':3,'xori':4,'ori':6,'andi':7,'slli':1,'srli':5,'srai':5}
def arithmetic(op,a,b):
    if op in ['add','addi']:return (a+b)&MASK
    if op=='sub':return (a-b)&MASK
    if op in ['and','andi']:return a&b
    if op in ['or','ori']:return a|b
    if op in ['xor','xori']:return a^b
    if op in ['sll','slli']:return (a<<(b&31))&MASK
    if op in ['srl','srli']:return a>>(b&31)
    if op in ['sra','srai']:return (signed(a)>>(b&31))&MASK
    if op in ['slt','slti']:return int(signed(a)<signed(b))
    if op in ['sltu','sltiu']:return int(a<b)
    raise ValueError(op)
def mapped(a):return BASE<=a<BASE+N or MMIO<=a<MMIO+4
def idx(a):return a-BASE if BASE<=a<BASE+N else N+a-MMIO
class MemoryProgram(Program):
    def run(self,fail_addr=-1,fail_write=-1,initial_data=None):
        regs=[0]*32;mem=(initial if initial_data is None else initial_data).copy();pc=0;trace=[];tx=[]
        words=[self.encode(ins,k*4) for k,ins in enumerate(self.ops)]
        for step in range(2000):
            if pc//4>=len(words):return words,trace,regs,mem,tx,[3,pc,pc]
            ins=self.ops[pc//4];op,*a=ins;rd=0;value=0;nxt=(pc+4)&MASK
            if op=='ebreak':return words,trace,regs,mem,tx,[9,pc,0]
            if op=='ecall':return words,trace,regs,mem,tx,[8,pc,0]
            if op=='raw':return words,trace,regs,mem,tx,[1,pc,0]
            if op in ii:rd=a[0];value=arithmetic(op,regs[a[1]],a[2]&MASK)
            elif op in rr:rd=a[0];value=arithmetic(op,regs[a[1]],regs[a[2]])
            elif op=='lui':rd=a[0];value=a[1]<<12
            elif op=='auipc':rd=a[0];value=(pc+(a[1]<<12))&MASK
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
        if op in rr:
            f7,f3=rr[op];rd,rs1,rs2=a
            return (f7<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|0x33
        if op in ii:
            rd,rs1,v=a
            if op in ['slli','srli','srai']:
                assert 0<=v<=31
                if op=='srai':v|=0x400
            return iword(v,rs1,rd,0x13,ii[op])
        if op=='auipc':return (a[1]<<12)|(a[0]<<7)|0x17
        if op in sizes:
            reg,rs1,off=a
            if op.startswith('l'):return iword(off,rs1,reg,0x03,f3s[op])
            v=off&4095
            return ((v>>5)<<25)|(reg<<20)|(rs1<<15)|(f3s[op]<<12)|((v&31)<<7)|0x23
        return super().encode(ins,pc)

