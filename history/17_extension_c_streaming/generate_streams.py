"""Deterministic stream fixtures; golden values come from integer arithmetic.
The CPU binary model is intentionally not used for asynchronous engines.
"""
from pathlib import Path
import json, random
from application_asm import Asm, words, assembly
R=Path(__file__).resolve().parent
M=0x10000000; S=0x10010000; D=0x20000300; A=0x20000400
def s8(x): return x-256 if x&128 else x
def dot(a,b): return sum(s8((a>>(8*k))&255)*s8((b>>(8*k))&255) for k in range(4))
def wr(p,address,value):
 p.li(28,address);p.li(29,value);p.emit('sw',29,28,0)
def cfg(p,base,a,b,dst,n):
 for off,val in [(8,a),(12,b),(16,dst),(20,n),(0,1)]:wr(p,base+off,val)
def poll(p,base,label):
 p.li(28,base);p.label(label);p.emit('lw',29,28,4);p.emit('andi',30,29,1);p.emit('bne',30,0,label)
def copy(p,src,dst,n,label):
 p.li(1,src);p.li(2,dst);p.li(3,n);p.label(label);p.emit('lw',4,1,0);p.emit('sw',4,2,0)
 for reg in [1,2]:p.emit('addi',reg,reg,4)
 p.emit('addi',3,3,-1);p.emit('bne',3,0,label)
def cpu_dot(p,a,b,dst,n,label):
 p.li(1,a);p.li(2,b);p.li(3,n);p.li(5,0);p.label(label)
 p.emit('lw',6,1,0);p.emit('lw',7,2,0);p.emit('DOT4ACC',5,6,7)
 for reg in [1,2]:p.emit('addi',reg,reg,4)
 p.emit('addi',3,3,-1);p.emit('bne',3,0,label);p.li(2,dst);p.emit('sw',5,2,0)
def finish(p):wr(p,0x20000000,1);p.emit('ebreak')
def initial():
 rng=random.Random(0xC001);ram=[rng.getrandbits(32) for _ in range(4096)];sp=[0xdeadbeef^k for k in range(1024)]
 # Include signed extrema and distinguish all buffers.
 ram[:8]=[0x80808080,0x7f7f7f7f,0xffffffff,0,0x807f00ff,1,0x12345678,0xa5a5a5a5]
 return ram,sp
cases=[]
def add(name,p,ram,sp,checks,**opts):
 i=len(cases);finish(p) if not opts.get('halt',9)!=9 else None
 meta=dict(id=i,name=name,halt=9,dma_status=-1,acc_status=-1,dma_progress=-1,acc_progress=-1,inject=0,concurrent=0,resettable=0,checks=len(checks));meta.update(opts)
 cases.append(meta);stem=R/'programs'/('stream_%03d'%i)
 for suffix,data in [('imem',words(p)),('ram',ram),('sp',sp)]:stem.with_suffix('.'+suffix).write_text(''.join('%08x\n'%(x&0xffffffff) for x in data))
 stem.with_suffix('.s').write_text(assembly(p))
 stem.with_suffix('.expected').write_text(''.join('%d %d %08x\n'%(region,index,value&0xffffffff) for region,index,value in checks))

def generate():
 for n in [1,4,16,64,256,512,1024]:
  for src,dst,direction in [(M,S,'main_sp'),(S,M+0x2000,'sp_main'),(M,M+0x2000,'main_main')]:
   for hw in [0,1]:
    ram,sp=initial();p=Asm();values=(ram if src==M else sp)[:n]
    if hw:cfg(p,D,src,0,dst,n);poll(p,D,'wait')
    else:copy(p,src,dst,n,'copy')
    region=1 if dst==S else 0;offset=0 if region else (dst-M)//4
    checks=[(region,offset+k,v) for k,v in enumerate(values)]
    add('COPY_%s_%s_%d'%(direction,'DMA' if hw else 'CPU',n),p,ram,sp,checks,dma_status=2 if hw else 0,dma_progress=n if hw else 0,resettable=hw)
  for src,where in [(M,'main'),(S,'scratch')]:
   for hw in [0,1]:
    ram,sp=initial();p=Asm();av=ram if src==M else sp;want=sum(dot(av[k],ram[1024+k]) for k in range(n))
    if hw:cfg(p,A,src,M+0x1000,M+0x3000,n);poll(p,A,'wait')
    else:cpu_dot(p,src,M+0x1000,M+0x3000,n,'dot')
    add('DOT_%s_%s_%d'%(where,'ACC' if hw else 'CPU',n),p,ram,sp,[(0,3072,want)],acc_status=2 if hw else 0,acc_progress=n if hw else 0,resettable=hw)
  for hw in [0,1]:
   ram,sp=initial();p=Asm();want=sum(dot(ram[k],ram[1024+k]) for k in range(n))
   if hw:cfg(p,D,M,0,S,n);poll(p,D,'dma');cfg(p,A,S,M+0x1000,M+0x3000,n);poll(p,A,'acc')
   else:copy(p,M,S,n,'copy');cpu_dot(p,S,M+0x1000,M+0x3000,n,'dot')
   add('CHAIN_%s_%d'%('DMA_ACC' if hw else 'CPU',n),p,ram,sp,[(1,k,ram[k]) for k in range(n)]+[(0,3072,want)],dma_status=2 if hw else 0,acc_status=2 if hw else 0,dma_progress=n if hw else 0,acc_progress=n if hw else 0,resettable=hw)
 # Full signed bounds, all inputs aliased legally, length maximum.
 for val in [0x80808080,0x7f7f7f7f,0x807f807f]:
  ram,sp=initial();ram[:1024]=[val]*1024;p=Asm();cfg(p,A,M,M,M+0x3000,1024);poll(p,A,'wait')
  add('DOT_ALIAS_BOUND_%08x'%val,p,ram,sp,[(0,3072,1024*dot(val,val))],acc_status=2,acc_progress=1024,resettable=1)
 for engine in [D,A]:
  for label,a,b,dst,n,cause in [('zero',M,M+0x1000,S,0,1),('too_many',M,M+0x1000,S,1025,1),('src_align',M+1,M+0x1000,S,4,2),('dst_align',M,M+0x1000,S+2,4,2),('imem',0,M+0x1000,S,4,3),('mmio',0x20000100,M+0x1000,S,4,3),('end_cross',M+0x3ffc,M+0x1000,S,2,3),('wrap',0xfffffffc,M+0x1000,S,2,3),('overlap',M,M+0x1000,M+4,4,4)]:
   ram,sp=initial();p=Asm();cfg(p,engine,a,b,dst,n);poll(p,engine,'wait')
   kw={'dma_status' if engine==D else 'acc_status':(cause<<8)|6,'dma_progress' if engine==D else 'acc_progress':0}
   add(('DMA' if engine==D else 'ACC')+'_INVALID_'+label,p,ram,sp,[(1,0,sp[0]),(0,3072,ram[3072])],**kw)
 # Disjoint simultaneous engines and unrelated CPU work.
 ram,sp=initial();p=Asm();cfg(p,D,M,0,S,256);cfg(p,A,M+0x2000,M+0x2400,M+0x3000,64)
 p.li(1,200);p.li(2,0);p.label('work');p.emit('addi',2,2,1);p.emit('addi',1,1,-1);p.emit('bne',1,0,'work');p.li(3,M+0x3800);p.emit('sw',2,3,0);poll(p,D,'dma');poll(p,A,'acc')
 want=sum(dot(ram[2048+k],ram[2304+k]) for k in range(64))
 add('CONCURRENT',p,ram,sp,[(1,k,ram[k]) for k in range(256)]+[(0,3072,want),(0,3584,200)],dma_status=2,acc_status=2,dma_progress=256,acc_progress=64,concurrent=1,resettable=1)
 for first in [D,A]:
  ram,sp=initial();p=Asm()
  if first==D:cfg(p,D,M,0,S,1024);cfg(p,A,S,M+0x1000,M+0x3000,4);poll(p,D,'dma');kw=dict(dma_status=2,acc_status=0x506,dma_progress=1024,acc_progress=0);checks=[(1,k,ram[k]) for k in range(1024)]
  else:cfg(p,A,M,M+0x1000,M+0x3000,256);cfg(p,D,M,0,S,4);poll(p,A,'acc');kw=dict(dma_status=0x506,acc_status=2,dma_progress=0,acc_progress=256);checks=[(0,3072,sum(dot(ram[k],ram[1024+k]) for k in range(256)))]
  add('CONFLICT_'+('DMA_FIRST' if first==D else 'ACC_FIRST'),p,ram,sp,checks,**kw)
 for label,engine,addr,op,val in [('dma_src_read',D,M,'lw',0),('dma_dst_byte',D,S+1,'sb',1),('acc_result_read',A,M+0x3000,'lw',0),('busy_count',D,D+20,'sw',1),('busy_start',D,D,'sw',1),('busy_clear',A,A,'sw',2)]:
  ram,sp=initial();p=Asm();cfg(p,engine,M,M+0x1000,S if engine==D else M+0x3000,256);p.li(1,addr);p.li(2,val);p.emit(op,2,1,0);p.emit('ebreak')
  kw=dict(halt=6 if op=='lw' else 7,dma_status=2 if engine==D else 0,acc_status=2 if engine==A else 0)
  checks=[(1,k,ram[k]) for k in range(256)] if engine==D else [(0,3072,sum(dot(ram[k],ram[1024+k]) for k in range(256)))]
  add('CPU_LOCK_'+label,p,ram,sp,checks,**kw)
 for engine in [D,A]:
  for label,off,op in [('readonly',4,'sw'),('narrow',8,'sb')]:
   ram,sp=initial();p=Asm();p.li(1,engine+off);p.li(2,1);p.emit(op,2,1,0);p.emit('ebreak');add(('DMA' if engine==D else 'ACC')+'_BAD_MMIO_'+label,p,ram,sp,[],halt=7,dma_status=0,acc_status=0)
 for inj,engine,cause in [(1,D,6),(2,D,7),(3,A,6),(4,A,6),(5,A,7),(6,A,8)]:
  ram,sp=initial();p=Asm();cfg(p,engine,M,M+0x1000,S if engine==D else M+0x3000,4);poll(p,engine,'wait')
  checks=[]
  if inj in [1,3,4,6]:checks=[(1,0,sp[0]),(0,3072,ram[3072])]
  if inj==2:checks=[(1,0,ram[0]),(1,1,sp[1])]
  if inj==5:checks=[(0,3072,sum(dot(ram[k],ram[1024+k]) for k in range(4)))]
  kw={'dma_status' if engine==D else 'acc_status':(cause<<8)|6,'dma_progress' if engine==D else 'acc_progress':4 if inj==5 else 0}
  add('FAULT_INJECTION_%d'%inj,p,ram,sp,checks,inject=inj,**kw)
 manifest=R/'verify'/'stream_cases.vec'
 manifest.write_text(str(len(cases))+'\n'+''.join('%d %s %d %d %d %d %d %d %d %d %d\n'%(c['id'],c['name'],c['halt'],c['dma_status'],c['acc_status'],c['dma_progress'],c['acc_progress'],c['inject'],c['concurrent'],c['resettable'],c['checks']) for c in cases))
 (R/'programs'/'stream_manifest.json').write_text(json.dumps(cases,indent=2))
 demo()
 rng=random.Random(0xcafe);vs=[]
 for i in range(16384):
  a=rng.getrandbits(32);b=rng.getrandbits(32)
  if i<8:a=[0,0x80808080,0x7f7f7f7f,0xffffffff,0x807f00ff,0x01010101,0xdeadbeef,0x7f807f80][i];b=0x80808080
  vs.append('%08x %08x %08x\n'%(a,b,dot(a,b)&0xffffffff))
 (R/'verify'/'pipeline.vec').write_text(''.join(vs))
 print('Generated',len(cases),'stream scenarios and 16384 pipeline vectors')

def demo():
 p=Asm();checks=[];rng=random.Random(0xC0DE);aa=[rng.getrandbits(32) for _ in range(64)];bb=[rng.getrandbits(32) for _ in range(64)]
 for k,(a,b) in enumerate(zip(aa,bb)):wr(p,M+4*k,a);wr(p,M+0x1000+4*k,b);wr(p,M+0x2000+4*k,b)
 cfg(p,D,M,0,S,64);poll(p,D,'copy_done')
 for k,v in enumerate(aa):checks.append((S+4*k,v))
 cfg(p,A,S,M+0x1000,M+0x3000,64)
 # Concurrent DMA has buffers distinct from the running accelerator.
 cfg(p,D,M+0x2000,0,M+0x2400,64)
 p.li(1,100);p.li(2,0);p.label('cpu_work');p.emit('addi',2,2,1);p.emit('addi',1,1,-1);p.emit('bne',1,0,'cpu_work');p.li(3,M+0x3800);p.emit('sw',2,3,0)
 poll(p,A,'acc_done');poll(p,D,'dma_done')
 checks += [(M+0x3000,sum(dot(a,b) for a,b in zip(aa,bb))),(M+0x3800,100),(D+4,2),(A+4,2),(D+24,64),(A+24,64)]
 checks += [(M+0x2400+4*k,v) for k,v in enumerate(bb)]
 # CPU narrow accesses to scratchpad once DMA releases it.
 wr(p,S+0x400,0);p.li(1,S+0x401);p.li(2,0x80);p.emit('sb',2,1,0);p.li(1,S+0x402);p.li(2,0x1234);p.emit('sh',2,1,0);checks.append((S+0x400,0x12348000))
 for k,(addr,want) in enumerate(checks,1):
  p.li(24,k);p.li(1,addr);p.emit('lw',2,1,0);p.li(3,want);p.emit('beq',2,3,'check_%d'%k);p.emit('jal',0,'failure');p.label('check_%d'%k)
 cfg(p,D,M,0,S,0);poll(p,D,'invalid_done')
 for number,expected in enumerate([0x106,0],len(checks)+1):
  if expected==0:wr(p,D,2)
  p.li(24,number);p.li(1,D+4);p.emit('lw',2,1,0);p.li(3,expected);p.emit('beq',2,3,'check_%d'%number);p.emit('jal',0,'failure');p.label('check_%d'%number)
 p.li(1,0x20000100)
 for k,ch in enumerate(b'C OK\r\n'):
  p.label('uart_%d'%k);p.emit('lw',2,1,4);p.emit('andi',2,2,1);p.emit('beq',2,0,'uart_%d'%k);p.li(2,ch);p.emit('sw',2,1,0)
 p.label('uart_end');p.emit('lw',2,1,4);p.emit('andi',2,2,1);p.emit('beq',2,0,'uart_end')
 wr(p,0x20000200,5);finish(p);p.label('failure');p.li(1,M+0x7fc);p.emit('sw',24,1,0);wr(p,0x20000200,15);wr(p,0x20000000,2);p.emit('ebreak')
 (R/'programs'/'stream_demo.mem').write_text(''.join('%08x\n'%w for w in words(p)))
 (R/'programs'/'stream_demo.s').write_text(assembly(p));(R/'programs'/'stream_demo.json').write_text(json.dumps(dict(words=len(words(p)),checks=len(checks)+2,dot=sum(dot(a,b) for a,b in zip(aa,bb))),indent=2))
if __name__=='__main__':generate()
