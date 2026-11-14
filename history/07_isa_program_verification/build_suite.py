from pathlib import Path
import json,random
from isa_model import MemoryProgram,BASE,MMIO,MASK,rr,ii,preds,sizes
root=Path(__file__).resolve().parent
names=list(rr)+list(ii)+['lui','auipc']+list(preds)+['jal','jalr']+['lb','lbu','lh','lhu','lw','sb','sh','sw','fence','ecall','ebreak']
assert len(names)==40
cases=[]
def save(name,p,focus=None,focus_pc=0,kind='directed'):
    words,trace,regs,mem,tx,stop=p.run()
    ram={j//4:sum(mem[j+k]<<(8*k) for k in range(4)) for j in range(0,16384,4)}
    ram={j:v for j,v in ram.items() if v}
    status=sum(mem[16384+k]<<(8*k) for k in range(4))
    repeat_raw=[t[4] for t in tx]
    if kind=='program':
        w2,t2,r2,m2,tx2,stop2=p.run(initial_data=mem[:16384]+[0]*4)
        assert (w2,t2,r2,m2,stop2)==(words,trace,regs,mem,stop)
        assert [t[:4]+t[5:] for t in tx2]==[t[:4]+t[5:] for t in tx]
        repeat_raw=[t[4] for t in tx2]
    if focus:
        assert any(t[0]==focus_pc for t in trace) or (stop[1]==focus_pc and stop[0] in [2,4,5,6,7,8,9]),(name,focus_pc,stop)
    cases.append(dict(name=name,kind=kind,focus=focus,focus_pc=focus_pc,words=words,trace=trace,regs=regs,
                      ram=ram,tx=tx,repeat_raw=repeat_raw,stop=stop,status=status,ops=p.ops,labels=p.labels))
def end(p):p.emit('ebreak')
rng=random.Random(20261007)
pairs=[(0,0),(1,MASK),(MASK,1),(0x7fffffff,1),(0x80000000,1),(0x80000000,0x7fffffff),
       (MASK,MASK),(5,3),(3,5),(0xaaaaaaaa,0x55555555),(0x80000000,31),(0x12345678,0),
       (1,32),(1,63),(0x80000000,0x80000001)]+[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(6)]
for op in rr:
    for j,(a,b) in enumerate(pairs):
        p=MemoryProgram();p.li(1,a);p.li(2,b);rd=[0,1,2,7][j%4];pc=len(p.ops)*4
        p.emit(op,rd,1,2);p.emit('addi',8,rd,1);end(p);save(f'{op} operands {a:08x}/{b:08x} rd={rd}',p,op,pc)
for op in ii:
    if op in ['slli','srli','srai']:vs=[0,1,15,31]
    else:vs=[-2048,-1,0,1,2047]
    for a in [0,1,MASK,0x80000000,0x7fffffff,0x12345678]:
        for j,v in enumerate(vs):
            p=MemoryProgram();p.li(1,a);rd=[0,1,7][j%3];pc=len(p.ops)*4;p.emit(op,rd,1,v)
            p.emit('addi',8,rd,1);end(p);save(f'{op} a={a:08x} immediate={v} rd={rd}',p,op,pc)
for op in ['lui','auipc']:
    for v in [0,1,0x7ffff,0x80000,0xfffff]:
        for rd in [0,7]:
            p=MemoryProgram();p.li(1,17);pc=len(p.ops)*4;p.emit(op,rd,v);end(p);save(f'{op} upper={v:05x} rd={rd}',p,op,pc)
for op in preds:
    for a,b in [(0,0),(MASK,1),(1,MASK),(7,7),(0x80000000,0x7fffffff),(0x7fffffff,0x80000000)]:
        p=MemoryProgram();p.li(1,a);p.li(2,b);pc=len(p.ops)*4;p.emit(op,1,2,'target')
        p.li(3,99);p.label('target');p.li(4,5);end(p);save(f'{op} compare {a:08x}/{b:08x}',p,op,pc)
    yes={'beq':(1,1),'bne':(1,2),'blt':(-1,1),'bge':(1,-1),'bltu':(1,2),'bgeu':(2,1)}[op]
    no={'beq':(1,2),'bne':(1,1),'blt':(1,-1),'bge':(-1,1),'bltu':(2,1),'bgeu':(1,2)}[op]
    for take,pair in [('taken',yes),('not_taken',no)]:
        p=MemoryProgram();p.li(1,pair[0]);p.li(2,pair[1]);pc=len(p.ops)*4;p.emit(op,1,2,2);end(p)
        save(f'{op} {take} misaligned target',p,op,pc)
for off in [4092,-4096]:
    p=MemoryProgram();p.emit('beq',0,0,off)
    # For positive offset, padded ROM words are illegal zero encodings, not a fetch error.
    if off>0:
        while len(p.ops)*4<off:p.emit('raw',0)
        end(p)
    save(f'BEQ displacement {off}',p,'beq',0)
for rd in [0,1,7]:
    p=MemoryProgram();p.emit('jal',rd,'target');p.li(31,99);p.label('target');p.li(3,5);end(p);save(f'JAL forward rd={rd}',p,'jal',0)
p=MemoryProgram();p.emit('jal',0,'start');p.label('back');p.li(10,9);p.emit('jal',0,'done');p.label('start')
pc=len(p.ops)*4;p.emit('jal',1,'back');p.label('done');end(p);save('JAL negative offset',p,'jal',pc)
for off in [2,1048572,-1048576]:
    p=MemoryProgram();p.emit('jal',1,off);save(f'JAL boundary {off}',p,'jal',0)
for base,off,rd in [(16,0,1),(17,0,1),(16,1,1),(24,-8,1),(16,0,5),(16,0,0),(19,0,1),(0xfffffffd,0,1),(1,2047,1),(2064,-2048,1)]:
    p=MemoryProgram();p.li(5,base);pc=len(p.ops)*4;p.emit('jalr',rd,5,off)
    target=((base+off)&MASK)&0xfffffffe
    if target in [16,2048]:
        while len(p.ops)*4<target:p.emit('raw',0)
        p.li(6,7);end(p)
    save(f'JALR base={base:08x} off={off} rd={rd}',p,'jalr',pc)
for op in ['lb','lbu','lh','lhu','lw']:
    lanes=range(4) if sizes[op]==1 else [0,2] if sizes[op]==2 else [0]
    for v in [0,MASK,0x80017f80,0x7fffffff]:
        for lane in lanes:
            p=MemoryProgram();p.li(1,BASE);p.li(2,v);p.emit('sw',2,1,0);pc=len(p.ops)*4
            p.emit(op,7,1,lane);p.emit('addi',8,7,1);end(p);save(f'{op} value={v:08x} lane={lane}',p,op,pc)
    for rd in [0,1]:
        p=MemoryProgram();p.li(1,BASE);p.li(2,0x89abcdef);p.emit('sw',2,1,0);pc=len(p.ops)*4
        p.emit(op,rd,1,0);end(p);save(f'{op} alias rd={rd}',p,op,pc)
for op in ['sb','sh','sw']:
    lanes=range(4) if sizes[op]==1 else [0,2] if sizes[op]==2 else [0]
    for v in [0,MASK,0x89abcdef,0x80000000]:
        for lane in lanes:
            p=MemoryProgram();p.li(1,BASE);p.li(2,0xa55a55aa);p.emit('sw',2,1,0);p.li(3,v)
            pc=len(p.ops)*4;p.emit(op,3,1,lane);p.emit('lw',7,1,0);end(p);save(f'{op} value={v:08x} lane={lane}',p,op,pc)
    p=MemoryProgram();p.li(1,BASE);pc=len(p.ops)*4;p.emit(op,0,1,0);end(p);save(f'{op} rs2 x0',p,op,pc)
for op in sizes:
    # A failing byte/halfword response must report the raw address, not the aligned bus word.
    lane=3 if sizes[op]==1 else 2 if sizes[op]==2 else 0
    p=MemoryProgram();p.li(1,BASE+16384);pc=len(p.ops)*4;p.emit(op,2,1,lane);end(p);save(f'{op} access error raw offset {lane}',p,op,pc)
    if sizes[op]>1:
        p=MemoryProgram();p.li(1,BASE);pc=len(p.ops)*4;p.emit(op,2,1,1);end(p);save(f'{op} misaligned',p,op,pc)
    if sizes[op]<4:
        p=MemoryProgram();p.li(1,MMIO);pc=len(p.ops)*4;p.emit(op,2,1,0);end(p);save(f'{op} narrow MMIO rejected',p,op,pc)
for op in ['fence','ecall','ebreak']:
    p=MemoryProgram();p.li(1,BASE);p.li(2,123);p.emit('sw',2,1,0);pc=len(p.ops)*4;p.emit(op)
    if op=='fence':p.emit('lw',3,1,0);end(p)
    save(f'{op} after completed store',p,op,pc)
for name,word in [('MUL',0x022083b3),('CSR',0x300013f3),('FENCE.I',0x0000100f),('bad SLLI',0x02009393),
                  ('bad JALR',0x000013e7),('bad branch',0x00002063),('bad load',0x00003083),('bad store',0x00003023),
                  ('malformed ECALL',0x000000f3),('zero word',0)]:
    p=MemoryProgram();p.li(1,77);p.emit('raw',word);save(f'illegal {name}',p,kind='error')

def finish_success(p):
    p.emit('fence');p.li(24,MMIO);p.li(25,1);p.emit('sw',25,24,0);end(p)
def program(name,p,assertions):
    finish_success(p);save(name,p,kind='program');c=cases[-1]
    for key,v in assertions.items():
        if key.startswith('x'):assert c['regs'][int(key[1:])]==v,(name,key,c['regs'])
        else:assert c['ram'].get(int(key),0)==v,(name,key,c['ram'])
    assert c['status']==1
    return c
p=MemoryProgram();p.li(8,BASE);p.emit('addi',9,8,0);p.li(10,0);p.li(11,1);p.li(12,12)
p.label('loop');p.emit('sw',10,9,0);p.emit('add',13,10,11);p.emit('addi',10,11,0);p.emit('addi',11,13,0)
p.emit('addi',9,9,4);p.emit('addi',12,12,-1);p.emit('bne',12,0,'loop')
fib=program('fibonacci_12',p,{str(k):v for k,v in enumerate([0,1,1,2,3,5,8,13,21,34,55,89])})
p=MemoryProgram();p.li(1,100);p.li(2,0);p.li(3,0);p.label('loop');p.emit('addi',2,2,1);p.emit('add',3,3,2)
p.emit('blt',2,1,'loop');p.li(8,BASE);p.emit('sw',3,8,0);program('loop_sum_100',p,{'x3':5050,'0':5050})
p=MemoryProgram();p.li(10,48);p.li(11,18);p.label('loop');p.emit('beq',10,11,'done');p.emit('bltu',10,11,'less')
p.emit('sub',10,10,11);p.emit('jal',0,'loop');p.label('less');p.emit('sub',11,11,10);p.emit('jal',0,'loop')
p.label('done');p.li(8,BASE);p.emit('sw',10,8,0);program('gcd_48_18',p,{'x10':6,'0':6})
p=MemoryProgram();p.li(2,BASE+16384);p.li(10,40);p.emit('jal',1,'outer');p.li(8,BASE);p.emit('sw',10,8,0);p.emit('jal',0,'done')
p.label('outer');p.emit('addi',2,2,-16);p.emit('sw',1,2,12);p.emit('jal',1,'inner')
p.emit('addi',10,10,1);p.emit('lw',1,2,12);p.emit('addi',2,2,16);p.emit('jalr',0,1,0)
p.label('inner');p.emit('addi',10,10,1);p.emit('jalr',0,1,0);p.label('done')
program('nested_call_aligned_stack',p,{'x10':42,'x2':BASE+16384,'0':42})
p=MemoryProgram();p.li(8,BASE);p.li(9,BASE+512);p.li(10,64);p.li(11,0)
p.label('fill');p.emit('sw',11,8,0);p.emit('addi',8,8,4);p.emit('addi',11,11,1);p.emit('blt',11,10,'fill')
p.li(8,BASE);p.li(11,0);p.li(12,0);p.label('copy');p.emit('lw',13,8,0);p.emit('sw',13,9,0);p.emit('add',12,12,13)
p.emit('addi',8,8,4);p.emit('addi',9,9,4);p.emit('addi',11,11,1);p.emit('blt',11,10,'copy')
program('memory_copy_64_checksum',p,{'x12':2016,**{str(128+k):k for k in range(64)}})
p=MemoryProgram();p.li(8,BASE);p.li(1,0x89abcdef);p.emit('sw',1,8,0);p.emit('lb',2,8,3)
p.emit('lbu',3,8,3);p.emit('lh',4,8,2);p.emit('lhu',5,8,2);p.emit('sb',0,8,1)
p.li(6,0x1234);p.emit('sh',6,8,2);p.emit('lw',7,8,0)
program('subword_signed_memory',p,{'x2':0xffffff89,'x3':137,'x4':0xffff89ab,'x5':0x89ab,'x7':0x123400ef,'0':0x123400ef})

coverage={op:[] for op in names}
for idx,c in enumerate(cases):
    if c['focus']:coverage[c['focus']].append(idx)
assert all(coverage.values())
(root/'suite.json').write_text(json.dumps(cases,indent=2))
(root/'coverage.json').write_text(json.dumps(coverage,indent=2))
lines=[str(len(cases))]
for idx,c in enumerate(cases):
    cause,pc,addr=c['stop'];focus=names.index(c['focus']) if c['focus'] else -1
    lines.append(f"{idx} {int(c['kind']=='program')} {focus} {c['focus_pc']:08x} {len(c['words'])} {len(c['trace'])} {len(c['tx'])} {len(c['ram'])} {cause} {pc:08x} {addr:08x} {c['status']:08x}")
    lines.extend(f'{w:08x}' for w in c['words'])
    lines.extend(f'{pc:08x} {w:08x} {rd} {v:08x} {nxt:08x}' for pc,w,rd,v,nxt in c['trace'])
    lines.extend(f'{r:08x}' for r in c['regs'])
    lines.extend(f'{k} {v:08x}' for k,v in c['ram'].items())
    lines.extend(f'{a:08x} {wr} {wd:08x} {mask:x} {raw:08x} {err} {c["repeat_raw"][j]:08x}' for j,(a,wr,wd,mask,raw,err) in enumerate(c['tx']))
(root/'verify/suite.vec').write_text('\n'.join(lines)+'\n')
(root/'suite_config.json').write_text(json.dumps(dict(cases=len(cases),runs=(len(cases)+6)*2,programs=6,names=names)))
print(f'{len(cases)} cases, {(len(cases)+6)*2} system runs; all {len(names)} instruction names have focused tests')
