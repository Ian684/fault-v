from pathlib import Path
import json
from program_model import MemoryProgram
from assembler_support import iword
from reference import OPS,encode,pack8

ROOT=Path(__file__).resolve().parent
vectors=json.loads((ROOT/'programs/benchmark_vectors.json').read_text())
rr={'sub':(0x20,0),'xor':(0,4),'or':(0,6),'sra':(0x20,5)}
ii={'andi':7,'slli':1,'srli':5,'srai':5}
class Asm(MemoryProgram):
    def encode(self,ins,pc):
        op,*a=ins
        if op in OPS:return encode(op,*a)
        if op in rr:
            f7,f3=rr[op];return (f7<<25)|(a[2]<<20)|(a[1]<<15)|(f3<<12)|(a[0]<<7)|0x33
        if op in ii:
            immediate=a[2]+(0x400 if op=='srai' else 0)
            return iword(immediate,a[1],a[0],f3=ii[op])
        return super().encode(ins,pc)

serial=0
def multiply(p):
    """Inlined signed magnitude shift/add, early exit, clobbers x5..7,x10,x11."""
    global serial
    serial+=1;t='mul_'+str(serial)
    p.emit('xor',5,10,11)
    p.emit('bge',10,0,t+'_a');p.emit('sub',10,0,10);p.label(t+'_a')
    p.emit('bge',11,0,t+'_b');p.emit('sub',11,0,11);p.label(t+'_b')
    p.li(6,0);p.label(t+'_loop');p.emit('beq',11,0,t+'_done')
    p.emit('andi',7,11,1);p.emit('beq',7,0,t+'_skip');p.emit('add',6,6,10);p.label(t+'_skip')
    p.emit('slli',10,10,1);p.emit('srli',11,11,1);p.emit('jal',0,t+'_loop')
    p.label(t+'_done');p.emit('bge',5,0,t+'_positive');p.emit('sub',6,0,6);p.label(t+'_positive')
    p.emit('addi',10,6,0)

def satadd(p):
    global serial
    serial+=1;t='sat_'+str(serial)
    p.emit('add',5,10,11);p.emit('xor',6,10,11);p.emit('blt',6,0,t+'_normal')
    p.emit('xor',6,10,5);p.emit('bge',6,0,t+'_normal')
    p.emit('srli',6,10,31);p.li(10,0x7fffffff);p.emit('add',10,10,6);p.emit('jal',0,t+'_end')
    p.label(t+'_normal');p.emit('addi',10,5,0);p.label(t+'_end')

def quantize(p):
    global serial
    serial+=1;t='qnt_'+str(serial)
    p.emit('sra',10,10,11);p.li(5,-128);p.emit('bge',10,5,t+'_high_check')
    p.li(10,-128);p.emit('jal',0,t+'_end')
    p.label(t+'_high_check');p.li(5,127);p.emit('bge',5,10,t+'_end')
    p.li(10,127);p.label(t+'_end')

def pack_window(p,offset):
    p.li(10,0)
    for i in range(4):
        p.emit('lbu',11,18,offset+i)
        if i:p.emit('slli',11,11,i*8)
        p.emit('or',10,10,11)

ram=bytearray(16384)
def fill(offset,items,size):
    for i,x in enumerate(items):ram[offset+i*size:offset+(i+1)*size]=(x&((1<<(size*8))-1)).to_bytes(size,'little')
fill(0,vectors['dot64']['a'],1);fill(64,vectors['dot64']['b'],1)
fill(256,vectors['fir8']['samples'],1);fill(320,vectors['fir8']['coefficients'],1)
fill(448,vectors['fir8']['expected'],4)
fill(768,vectors['fir16']['samples'],2);fill(832,vectors['fir16']['coefficients'],2)
fill(1280,vectors['satadd64']['a'],4);fill(1536,vectors['satadd64']['b'],4)
for n in range(16):
    for k in (0,4):fill(2048+n*8+k,[pack8(vectors['fir8']['samples'][n+k:n+k+4])],4)
(ROOT/'programs/inputs.mem').write_text(''.join(f'{int.from_bytes(ram[i:i+4],"little"):08x}\n' for i in range(0,16384,4)))

workloads=['DOT64','FIR8_RAW','FIR8_PACKED','FIR16','QNT16','SATADD64']
manifest=[]
coefregs=[8,9,12,13,14,15,16,17]
for name in workloads:
    for custom in (False,True):
        p=Asm();p.label('kernel_begin');p.li(21,0x10000000)
        if name=='DOT64':
            p.li(18,0x10000000);p.li(19,0x10000040);p.li(20,16 if custom else 64);p.li(22,0)
            p.label('outer')
            if custom:p.emit('lw',10,18,0);p.emit('lw',11,19,0);p.emit('DOT4',10,10,11)
            else:p.emit('lb',10,18,0);p.emit('lb',11,19,0);multiply(p)
            p.emit('add',22,22,10)
            p.emit('addi',18,18,4 if custom else 1);p.emit('addi',19,19,4 if custom else 1)
            p.emit('addi',20,20,-1);p.emit('bne',20,0,'outer');p.emit('sw',22,21,128)
            outputs=[(128,vectors['dot64']['expected'])];expected_custom=16
        elif name in ['FIR8_RAW','FIR8_PACKED','FIR16']:
            size=2 if name=='FIR16' else 1
            input_offset=768 if size==2 else 2048 if name=='FIR8_PACKED' else 256
            coef_offset=832 if size==2 else 320
            out_offset=896 if size==2 else 384
            p.li(18,0x10000000+input_offset);p.li(19,0x10000000+out_offset);p.li(20,16)
            if custom and size==1:
                p.emit('lw',26,21,coef_offset);p.emit('lw',27,21,coef_offset+4)
            else:
                for k,reg in enumerate(coefregs):p.emit('lh' if size==2 else 'lb',reg,21,coef_offset+k*size)
            p.label('outer');p.li(22,0)
            if custom and size==1:
                for k,c in [(0,26),(4,27)]:
                    if name=='FIR8_RAW':pack_window(p,k)
                    else:p.emit('lw',10,18,k)
                    p.emit('DOT4',10,10,c);p.emit('add',22,22,10)
            else:
                if name=='FIR8_PACKED':p.emit('lw',24,18,0);p.emit('lw',25,18,4)
                for k,reg in enumerate(coefregs):
                    if name=='FIR8_PACKED':
                        source=24 if k<4 else 25;shift=24-(k%4)*8
                        if shift:p.emit('slli',10,source,shift)
                        else:p.emit('addi',10,source,0)
                        p.emit('srai',10,10,24)
                    else:p.emit('lh' if size==2 else 'lb',10,18,k*size)
                    if custom:p.emit('MUL16',10,10,reg)
                    else:p.emit('addi',11,reg,0);multiply(p)
                    p.emit('add',22,22,10)
            p.emit('sw',22,19,0);p.emit('addi',18,18,8 if name=='FIR8_PACKED' else size)
            p.emit('addi',19,19,4);p.emit('addi',20,20,-1);p.emit('bne',20,0,'outer')
            key='fir16' if size==2 else 'fir8';outputs=[(out_offset+i*4,x) for i,x in enumerate(vectors[key]['expected'])]
            expected_custom=128 if size==2 else 32
        elif name=='QNT16':
            p.li(18,0x100001c0);p.li(19,0x10000200);p.li(20,16);p.li(11,3);p.label('outer')
            p.emit('lw',10,18,0)
            if custom:p.emit('QNT8',10,10,11)
            else:quantize(p)
            p.emit('sw',10,19,0);p.emit('addi',18,18,4);p.emit('addi',19,19,4)
            p.emit('addi',20,20,-1);p.emit('bne',20,0,'outer')
            outputs=[(512+i*4,x) for i,x in enumerate(vectors['fir8']['quantized'])];expected_custom=16
        else:
            p.li(18,0x10000500);p.li(19,0x10000600);p.li(23,0x10000700);p.li(20,64);p.label('outer')
            p.emit('lw',10,18,0);p.emit('lw',11,19,0)
            if custom:p.emit('ADDSAT',10,10,11)
            else:satadd(p)
            p.emit('sw',10,23,0);p.emit('addi',18,18,4);p.emit('addi',19,19,4);p.emit('addi',23,23,4)
            p.emit('addi',20,20,-1);p.emit('bne',20,0,'outer')
            outputs=[(1792+i*4,x) for i,x in enumerate(vectors['satadd64']['expected_u32'])];expected_custom=64
        p.label('kernel_end');p.emit('addi',0,0,0)
        p.li(21,0x20000000);p.li(10,1);p.emit('sw',10,21,0);p.emit('ebreak')
        words=[]
        for i,ins in enumerate(p.ops):
            if ins[0] in ['beq','bne','blt','bge','bltu','bgeu']:
                off=p.offset(ins[3],i*4);assert off%2==0 and -4096<=off<=4094
            words.append(p.encode(ins,i*4))
        assert len(words)<=4096
        if not custom:assert all(w&127!=0x0b and not(w&127==0x33 and w>>25==1) for w in words)
        id=len(manifest);stem=name.lower()+('_custom' if custom else '_rv32i')
        (ROOT/'programs'/f'{stem}.mem').write_text(''.join(f'{w:08x}\n' for w in words+[0]*(4096-len(words))))
        labelmap={v:k for k,v in p.labels.items()};lines=['.section .text','.globl _start','_start:']
        for i,ins in enumerate(p.ops):
            if i*4 in labelmap:lines.append(labelmap[i*4]+':')
            op,*a=ins
            if op in OPS:s=f'.insn r 0x0b, {OPS[op]}, 0, x{a[0]}, x{a[1]}, x{a[2]} # {op}'
            elif op in ['lw','lh','lb','lbu','sw']:s=f'{op} x{a[0]}, {a[2]}(x{a[1]})'
            elif op in ['beq','bne','blt','bge']:s=f'{op} x{a[0]}, x{a[1]}, {a[2]}'
            elif op=='jal':s=f'jal x{a[0]}, {a[1]}'
            elif op=='lui':s=f'lui x{a[0]}, 0x{a[1]:x}'
            elif op=='ebreak':s=op
            else:s=f'{op} x{a[0]}, x{a[1]}, {a[2]}'
            lines.append('    '+s)
        (ROOT/'programs'/f'{stem}.S').write_text('\n'.join(lines)+'\n')
        manifest.append({'id':id,'workload':name,'variant':'custom' if custom else 'rv32i','image':stem+'.mem','words':len(words),'begin_pc':0,'end_pc':p.labels['kernel_end'],'halt_pc':(len(words)-1)*4,'custom_retired':expected_custom if custom else 0,'outputs':[(off//4,x&0xffffffff) for off,x in outputs]})
(ROOT/'programs/manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
lines=[str(len(manifest))]
for m in manifest:
    lines.append(f"{m['id']} ../programs/{m['image']} {m['end_pc']:08x} {m['halt_pc']:08x} {m['custom_retired']} {len(m['outputs'])}")
    lines.extend(f'{index} {value:08x}' for index,value in m['outputs'])
(ROOT/'verify/benchmark.vec').write_text('\n'.join(lines)+'\n')
print('Generated',len(manifest),'paired benchmark programs; maximum ROM words',max(m['words'] for m in manifest))
