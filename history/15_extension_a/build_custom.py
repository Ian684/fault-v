from pathlib import Path
import json,random
from program_model import MemoryProgram
from assembler_support import iword
from reference import OPS,execute,encode,pack8

ROOT=Path(__file__).resolve().parent
class CustomProgram(MemoryProgram):
    def encode(self,ins,pc):
        op,*a=ins
        if op in OPS:return encode(op,*a)
        if op in ['andi','slli']:
            return iword(a[2],a[1],a[0],f3=7 if op=='andi' else 1)
        if op=='or':return (a[2]<<20)|(a[1]<<15)|(6<<12)|(a[0]<<7)|0x33
        return super().encode(ins,pc)

def small_model(p):
    regs=[0]*32;ram=0;trace=[];customs=0
    words=[p.encode(ins,i*4) for i,ins in enumerate(p.ops)]
    for i,ins in enumerate(p.ops):
        op,*a=ins;rd=0;val=0
        if op=='ebreak':return words,trace,regs,9,i*4,ram,customs
        if op=='raw':return words,trace,regs,1,i*4,ram,customs
        if op=='lui':rd=a[0];val=a[1]<<12
        elif op=='addi':rd=a[0];val=(regs[a[1]]+a[2])&0xffffffff
        elif op in OPS:rd=a[0];val=execute(op,regs[a[1]],regs[a[2]],regs[rd]);customs+=1
        elif op=='sw':ram=regs[a[0]]
        elif op=='lw':rd=a[0];val=ram
        else:raise ValueError(ins)
        if rd:regs[rd]=val
        regs[0]=0
        trace.append((i*4,words[i],rd, val if rd else 0))
    raise AssertionError('No terminal instruction')

cases=[]
def case(op,a,b,rd=5,rs1=1,rs2=2):
    p=CustomProgram();p.li(1,a);p.li(2,b)
    if rd not in [0,1,2]:p.li(rd,0x7ffffffe)
    p.emit(op,rd,rs1,rs2);p.emit('addi',8,rd,1)
    p.li(31,0x10000000);p.emit('sw',8,31,0);p.emit('lw',9,31,0);p.emit('ebreak')
    cases.append(small_model(p))
for v in json.loads((ROOT/'programs/directed_vectors.json').read_text()):case(v['op'],int(v['a'],16),int(v['b'],16))
rng=random.Random(0x1718)
for op in OPS:
    for _ in range(64):case(op,rng.getrandbits(32),rng.getrandbits(32),rng.choice([0,1,2,5]))
    for rd,rs1,rs2 in [(3,1,2),(1,1,2),(2,1,2),(1,1,1),(0,1,2),(3,0,2),(3,1,0)]:case(op,0x80808080,0x01010101,rd,rs1,rs2)
p=CustomProgram();p.li(1,0x80808080);p.li(2,0x04030201)
for _ in range(4):
    for op in OPS:p.emit(op,1,1,2)
p.emit('ebreak');cases.append(small_model(p))
for f7 in range(128):
    for f3 in range(8):
        if (f7==0 and f3<4) or f7==1:continue
        p=CustomProgram();p.li(1,0x12345678);p.li(2,0x89abcdef)
        p.emit('raw',(f7<<25)|(2<<20)|(1<<15)|(f3<<12)|(5<<7)|0x0b)
        p.emit('ebreak');cases.append(small_model(p))
lines=[str(len(cases))]
for words,trace,regs,cause,stop,ram,customs in cases:
    lines.append(f'{len(words)} {len(trace)} {cause} {stop:08x} {ram:08x} {customs}')
    lines+= [f'{x:08x}' for x in words]
    lines+= [f'{pc:08x} {word:08x} {rd} {val:08x}' for pc,word,rd,val in trace]
    lines.append(' '.join(f'{x:08x}' for x in regs))
(ROOT/'verify/cpu.vec').write_text('\n'.join(lines)+'\n')

# A single self-checking FPGA program exercises all four workloads.
vectors=json.loads((ROOT/'programs/benchmark_vectors.json').read_text())
p=CustomProgram();p.li(20,0x10000000)
expected={};check_id=0
def store_bytes(values,offset,size):
    for i,value in enumerate(values):
        p.li(10,value);p.emit('sb' if size==1 else 'sh',10,20,offset+i*size)
def verify(rd,value,offset):
    global check_id
    check_id+=1
    p.li(30,check_id);p.li(7,value)
    p.emit('beq',rd,7,f'ok_{check_id}');p.emit('jal',0,'fail');p.label(f'ok_{check_id}')
    p.emit('sw',rd,20,offset);expected[offset]=value&0xffffffff
def packed_window(offset):
    p.li(11,0)
    for i in range(4):
        p.emit('lbu',12,20,offset+i)
        if i:p.emit('slli',12,12,i*8)
        p.emit('or',11,11,12)
store_bytes(vectors['dot64']['a'],0,1);store_bytes(vectors['dot64']['b'],64,1)
p.li(3,0)
for i in range(0,64,4):
    p.emit('lw',1,20,i);p.emit('lw',2,20,64+i);p.emit('DOT4',5,1,2);p.emit('add',3,3,5)
verify(3,vectors['dot64']['expected'],128)
f=vectors['fir8'];store_bytes(f['samples'],256,1)
p.li(1,pack8(f['coefficients'][:4]));p.li(2,pack8(f['coefficients'][4:]));p.li(8,3)
for n in range(16):
    packed_window(256+n);p.emit('DOT4',5,11,1)
    packed_window(260+n);p.emit('DOT4',6,11,2);p.emit('add',5,5,6)
    verify(5,f['expected'][n],384+n*4)
    p.emit('QNT8',6,5,8);verify(6,f['quantized'][n],448+n*4)
f=vectors['fir16'];store_bytes(f['samples'],768,2);store_bytes(f['coefficients'],832,2)
for n in range(16):
    p.li(3,0)
    for k in range(8):
        p.emit('lh',1,20,768+(n+k)*2);p.emit('lh',2,20,832+k*2)
        p.emit('MUL16',5,1,2);p.emit('add',3,3,5)
    verify(3,f['expected'][n],896+n*4)
f=vectors['satadd64']
for i,(a,b,want) in enumerate(zip(f['a'],f['b'],f['expected_u32'])):
    p.li(1,a);p.li(2,b);p.emit('ADDSAT',5,1,2);verify(5,want,1024+i*4)
# Directed corner cases are also checked on the actual FPGA.
for v in json.loads((ROOT/'programs/directed_vectors.json').read_text()):
    p.li(1,int(v['a'],16));p.li(2,int(v['b'],16));p.li(5,0);p.emit(v['op'],5,1,2)
    verify(5,int(v['expected'],16),1536+(check_id-113)*4)
# Keep serial output within the UART Lite's 16-byte FIFO.
p.li(21,0x20000100)
for i,byte in enumerate(b'DSP OK\r\n'):
    p.li(10,byte);p.label(f'wait_{i}');p.emit('lw',11,21,4);p.emit('andi',11,11,1)
    p.emit('beq',11,0,f'wait_{i}');p.emit('sw',10,21,0)
p.label('drain');p.emit('lw',11,21,4);p.emit('andi',11,11,1);p.emit('beq',11,0,'drain')
p.li(21,0x20000200);p.li(10,5);p.emit('sw',10,21,0)
p.li(21,0x20000000);p.li(10,1);p.emit('sw',10,21,0);p.emit('ebreak')
p.label('fail');p.li(21,0x10000000);p.emit('sw',30,21,2044)
p.li(21,0x20000200);p.li(10,15);p.emit('sw',10,21,0)
p.li(21,0x20000000);p.li(10,2);p.emit('sw',10,21,0);p.emit('ebreak')
words=[p.encode(ins,k*4) for k,ins in enumerate(p.ops)]
assert len(words)<=4096
for k,ins in enumerate(p.ops):
    if ins[0] in ['beq','bne']:
        displacement=p.offset(ins[3],k*4)
        assert -4096<=displacement<=4094 and displacement%2==0
    if ins[0]=='jal':
        displacement=p.offset(ins[2],k*4)
        assert -1048576<=displacement<=1048574 and displacement%2==0
(ROOT/'programs/custom_demo.mem').write_text(''.join(f'{w:08x}\n' for w in words+[0]*(4096-len(words))))
labels={v:k for k,v in p.labels.items()};asm=['.section .text','.globl _start','_start:']
for k,ins in enumerate(p.ops):
    if k*4 in labels:asm.append(labels[k*4]+':')
    op,*a=ins
    if op in OPS:s=f'.insn r 0x0b, {OPS[op] if OPS[op]<4 else OPS[op]-4}, {0 if OPS[op]<4 else 1}, x{a[0]}, x{a[1]}, x{a[2]} # {op}'
    elif op in ['lw','lh','lbu','sw','sh','sb']:s=f'{op} x{a[0]}, {a[2]}(x{a[1]})'
    elif op in ['beq','bne']:s=f'{op} x{a[0]}, x{a[1]}, {a[2]}'
    elif op=='lui':s=f'lui x{a[0]}, 0x{a[1]:x}'
    elif op in ['addi','andi','slli']:s=f'{op} x{a[0]}, x{a[1]}, {a[2]}'
    elif op in ['or','add']:s=f'{op} x{a[0]}, x{a[1]}, x{a[2]}'
    else:s=op
    asm.append('    '+s)
(ROOT/'programs/custom_demo.S').write_text('\n'.join(asm)+'\n')
(ROOT/'programs/expected_outputs.json').write_text(json.dumps({str(k):v for k,v in expected.items()},indent=2))
(ROOT/'verify/demo_outputs.vec').write_text(str(len(expected))+'\n'+''.join(f'{off//4} {v:08x}\n' for off,v in expected.items()))
manifest={'cpu_cases_per_mode':len(cases),'custom_demo_words':len(words),'self_checks':check_id,'stored_outputs':len(expected),'custom_instructions':sum(ins[0] in OPS for ins in p.ops),'success_text':'DSP OK\r\n','success_status':1,'success_halt_cause':9}
(ROOT/'programs/demo_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest))
