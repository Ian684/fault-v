"""Original six pairs plus eight extension pairs; all inputs and answers explicit."""
from pathlib import Path
import json,random
import build_benchmarks as B
from reference import OPS,execute
R=Path(__file__).resolve().parent
B.rr.update({'sll':(0,1),'srl':(0,5)})
serial=0
def tag(prefix):
 global serial
 serial+=1
 return f'{prefix}_{serial}'
def lane(p,rd,source,index,width,signed=True):
 if signed:
  shift=32-width-index*width
  if shift:p.emit('slli',rd,source,shift)
  else:p.emit('addi',rd,source,0)
  p.emit('srai',rd,rd,32-width)
 else:
  p.emit('srli',rd,source,index*width);p.emit('andi',rd,rd,(1<<width)-1)
def clip8(p,reg):
 t=tag('clip')
 p.li(5,-128);p.emit('bge',reg,5,t+'_high');p.li(reg,-128);p.emit('jal',0,t+'_end')
 p.label(t+'_high');p.li(5,127);p.emit('bge',5,reg,t+'_end');p.li(reg,127);p.label(t+'_end')
def software(p,op):
 if op in ['DOT4ACC','DOT8','DOT4SU']:
  if op!='DOT4ACC':p.li(22,0)
  width=4 if op=='DOT8' else 8
  for k in range(32//width):
   lane(p,10,24,k,width);lane(p,11,25,k,width,op!='DOT4SU')
   B.multiply(p);p.emit('add',22,22,10)
 elif op=='MAC16':
  lane(p,10,24,0,16);lane(p,11,25,0,16);B.multiply(p);p.emit('add',22,22,10)
 elif op in ['ADD8SAT','SUB8SAT']:
  p.li(30,0)
  for k in range(4):
   lane(p,10,24,k,8);lane(p,11,25,k,8)
   p.emit('add' if op=='ADD8SAT' else 'sub',10,10,11);clip8(p,10);p.emit('andi',10,10,255)
   if k:p.emit('slli',10,10,k*8)
   p.emit('or',30,30,10)
  p.emit('addi',22,30,0)
 elif op=='DOT2SAT':
  lane(p,10,24,0,16);lane(p,11,25,0,16);B.multiply(p);p.emit('addi',28,10,0)
  lane(p,10,24,1,16);lane(p,11,25,1,16);B.multiply(p)
  p.emit('addi',11,10,0);p.emit('addi',10,28,0);B.satadd(p);p.emit('addi',22,10,0)
 elif op=='RQNT8':
  # The benchmark's specified inputs have exact products fitting signed INT32.
  # General ISA correctness (full 48-bit products) is checked separately by unit/CPU tests.
  p.emit('addi',10,24,0);lane(p,11,25,0,16);B.multiply(p)
  p.emit('srli',12,25,16);p.emit('andi',12,12,31)
  p.emit('slli',13,25,3);p.emit('srai',13,13,24)
  p.emit('srai',14,10,31);t=tag('round')
  p.emit('bge',10,0,t+'_abs');p.emit('sub',10,0,10);p.label(t+'_abs')
  p.emit('beq',12,0,t+'_shift');p.emit('addi',16,12,-1);p.li(15,1)
  p.emit('sll',15,15,16);p.emit('add',10,10,15);p.label(t+'_shift');p.emit('srl',10,10,12)
  p.emit('bge',14,0,t+'_positive');p.emit('sub',10,0,10);p.label(t+'_positive')
  p.emit('add',10,10,13);clip8(p,10);p.emit('addi',22,10,0)
 else:raise ValueError(op)

rng=random.Random(0xa1919)
datasets={}
for w,op in enumerate(list(OPS)[4:]):
 av=[rng.getrandbits(32) for _ in range(16)];bv=[rng.getrandbits(32) for _ in range(16)]
 cv=[rng.getrandbits(32) for _ in range(16)]
 if op=='RQNT8':
  av=[-10000,-4097,-257,-129,-3,-1,0,1,3,5,127,128,257,4097,10000,32767]
  bv=[(m&65535)|(s<<16)|((z&255)<<21) for m,s,z in zip([-123,1,3,17]*4,[0,1,3,8,16,31,0,1]*2,[-128,-1,0,1,127,-1,0,1]*2)]
  assert all(abs(a*((b&65535)-65536 if b&32768 else b&65535))<2**31 for a,b in zip(av,bv))
 if op=='DOT2SAT':av[0]=bv[0]=0x80008000
 if op=='DOT8':av[0]=bv[0]=0x88888888
 if op=='DOT4SU':av[0]=0x80808080;bv[0]=0xffffffff
 output=[execute(op,a,b,c) for a,b,c in zip(av,bv,cv)]
 offset=4096+w*256;outoff=6144+w*64
 B.fill(offset,av,4);B.fill(offset+64,bv,4);B.fill(offset+128,cv,4)
 datasets[op]=dict(a=av,b=bv,acc=cv,expected=output,input_offset=offset,output_offset=outoff)
 for custom in [False,True]:
  p=B.Asm();p.label('kernel_begin');p.li(21,0x10000000)
  p.li(18,0x10000000+offset);p.li(19,0x10000000+offset+64)
  p.li(23,0x10000000+offset+128);p.li(26,0x10000000+outoff);p.li(20,16)
  p.label('outer');p.emit('lw',24,18,0);p.emit('lw',25,19,0)
  accumulate=op in ['DOT4ACC','MAC16']
  if accumulate:p.emit('lw',22,23,0)
  if custom:p.emit(op,22,24,25)
  else:software(p,op)
  p.emit('sw',22,26,0);p.emit('addi',18,18,4);p.emit('addi',19,19,4)
  if accumulate:p.emit('addi',23,23,4)
  p.emit('addi',26,26,4);p.emit('addi',20,20,-1);p.emit('bne',20,0,'outer')
  end_pc=len(p.ops)*4;p.label('kernel_end');p.li(30,0x20000000);p.li(29,1);p.emit('sw',29,30,0);p.emit('ebreak')
  words=[p.encode(ins,i*4) for i,ins in enumerate(p.ops)];assert len(words)<=4096
  if not custom:assert all((x&127)!=11 and not((x&127)==0x33 and x>>25==1) for x in words)
  for i,ins in enumerate(p.ops):
   if ins[0] in ['beq','bne','blt','bge','bltu','bgeu']:
    off=p.offset(ins[3],i*4);assert -4096<=off<=4094 and off%4==0
  name=op.lower()+('_custom' if custom else '_rv32i')
  (R/'programs'/f'{name}.mem').write_text(''.join(f'{x:08x}\n' for x in words+[0]*(4096-len(words))))
  labels={v:k for k,v in p.labels.items()};asm=['.section .text','.globl _start','_start:']
  for i,ins in enumerate(p.ops):
   if i*4 in labels:asm.append(labels[i*4]+':')
   inst,*args=ins
   if inst in OPS:
    n=OPS[inst];line=f'.insn r 0x0b, {n if n<4 else n-4}, {0 if n<4 else 1}, x{args[0]}, x{args[1]}, x{args[2]} # {inst}'
   elif inst in ['lw','sw']:line=f'{inst} x{args[0]}, {args[2]}(x{args[1]})'
   elif inst in ['beq','bne','blt','bge','bltu','bgeu']:line=f'{inst} x{args[0]}, x{args[1]}, {args[2]}'
   elif inst=='jal':line=f'jal x{args[0]}, {args[1]}'
   elif inst=='lui':line=f'lui x{args[0]}, 0x{args[1]:x}'
   elif inst=='ebreak':line=inst
   elif inst in ['addi','andi','slli','srli','srai']:line=f'{inst} x{args[0]}, x{args[1]}, {args[2]}'
   else:line=f'{inst} '+', '.join(f'x{x}' for x in args)
   asm.append('    '+line)
  (R/'programs'/f'{name}.S').write_text('\n'.join(asm)+'\n')
  B.manifest.append(dict(id=len(B.manifest),workload=op+'_16',variant='custom' if custom else 'rv32i',image=f'{name}.mem',begin_pc=0,end_pc=end_pc,halt_pc=(len(words)-1)*4,custom_retired=16 if custom else 0,outputs=[(outoff//4+i,x) for i,x in enumerate(output)],words=len(words)))

(R/'programs/inputs.mem').write_text(''.join(f'{int.from_bytes(B.ram[i:i+4],"little"):08x}\n' for i in range(0,16384,4)))
(R/'programs/extension_vectors.json').write_text(json.dumps(datasets,indent=2))
(R/'programs/manifest.json').write_text(json.dumps(B.manifest,indent=2))
lines=[str(len(B.manifest))]
for m in B.manifest:
 lines.append(f"{m['id']} ../programs/{m['image']} {m['end_pc']:08x} {m['halt_pc']:08x} {m['custom_retired']} {len(m['outputs'])}")
 lines.extend(f"{index} {value:08x}" for index,value in m['outputs'])
(R/'verify/benchmark.vec').write_text('\n'.join(lines)+'\n')
print('Generated',len(B.manifest),'benchmark images; max',max(m['words'] for m in B.manifest),'words.')
