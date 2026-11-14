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

