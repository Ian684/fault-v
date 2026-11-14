"""Readable application generators. No changes to CPU RTL or custom encodings."""
from program_model import MemoryProgram
from assembler_support import iword
from reference import OPS,encode
BASE=0x10000000
class Asm(MemoryProgram):
 def encode(self,ins,pc):
  op,*a=ins
  if op in OPS:return encode(op,*a)
  rr={'sub':(0x20,0),'xor':(0,4),'or':(0,6),'sll':(0,1),'srl':(0,5),'sra':(0x20,5)}
  if op in rr:
   f7,f3=rr[op];return (f7<<25)|(a[2]<<20)|(a[1]<<15)|(f3<<12)|(a[0]<<7)|0x33
  if op in ['andi','slli','srli','srai']:
   f3=7 if op=='andi' else 1 if op=='slli' else 5
   return iword(a[2]+(0x400 if op=='srai' else 0),a[1],a[0],f3=f3)
  return super().encode(ins,pc)
 def append(self,other,prefix):
  origin=len(self.ops)*4
  self.labels.update({prefix+k:origin+v for k,v in other.labels.items()})
  for ins in other.ops:self.ops.append(tuple(prefix+x if isinstance(x,str) and i>0 else x for i,x in enumerate(ins)))

serial=0
def tag(name):
 global serial
 serial+=1;return name+'_'+str(serial)
def multiply(p):
 # Inline signed magnitude shift/add; x10,x11 in, x10 out; scratch x5..7.
 t=tag('mul');p.emit('xor',5,10,11)
 p.emit('bge',10,0,t+'a');p.emit('sub',10,0,10);p.label(t+'a')
 p.emit('bge',11,0,t+'b');p.emit('sub',11,0,11);p.label(t+'b')
 p.li(6,0);p.label(t+'loop');p.emit('beq',11,0,t+'done')
 p.emit('andi',7,11,1);p.emit('beq',7,0,t+'skip');p.emit('add',6,6,10);p.label(t+'skip')
 p.emit('slli',10,10,1);p.emit('srli',11,11,1);p.emit('jal',0,t+'loop')
 p.label(t+'done');p.emit('bge',5,0,t+'positive');p.emit('sub',6,0,6);p.label(t+'positive');p.emit('addi',10,6,0)
def clip(p,reg,width):
 t=tag('clip');p.li(5,-(1<<(width-1)));p.emit('bge',reg,5,t+'high')
 p.li(reg,-(1<<(width-1)));p.emit('jal',0,t+'end');p.label(t+'high')
 p.li(5,(1<<(width-1))-1);p.emit('bge',5,reg,t+'end');p.li(reg,(1<<(width-1))-1);p.label(t+'end')
def requant(p):
 # x10 INT32 input, x25 packed control, x10 sign-extended INT8 output.
 p.emit('slli',11,25,16);p.emit('srai',11,11,16);multiply(p)
 p.emit('srli',12,25,16);p.emit('andi',12,12,31);p.emit('slli',13,25,3);p.emit('srai',13,13,24)
 p.emit('srai',14,10,31);t=tag('round');p.emit('bge',10,0,t+'abs');p.emit('sub',10,0,10);p.label(t+'abs')
 p.emit('beq',12,0,t+'shift');p.emit('addi',16,12,-1);p.li(15,1);p.emit('sll',15,15,16);p.emit('add',10,10,15)
 p.label(t+'shift');p.emit('srl',10,10,12);p.emit('bge',14,0,t+'pos');p.emit('sub',10,0,10);p.label(t+'pos')
 p.emit('add',10,10,13);clip(p,10,8)
def relu(p,reg):
 t=tag('relu');p.emit('bge',reg,0,t);p.li(reg,0);p.label(t)
def pack(p,rd,ptr,off,count):
 p.li(rd,0)
 for i in range(count):
  p.emit('lbu',10,ptr,off+i)
  if i:p.emit('slli',10,10,i*8)
  p.emit('or',rd,rd,10)

def conv(p,custom):
 p.li(18,BASE);p.li(26,BASE+0x1000);p.li(27,BASE+0x800);p.li(20,8)
 p.label('conv_position');p.li(19,BASE+0x40);p.li(28,BASE+0x80);p.li(29,BASE+0x90);p.li(23,3)
 p.label('conv_channel');p.emit('lw',22,28,0)
 if custom:
  pack(p,24,18,0,4);pack(p,25,19,0,4);p.emit('DOT4ACC',22,24,25)
  pack(p,24,18,4,2);pack(p,25,19,4,2);p.emit('DOT4ACC',22,24,25)
 else:
  for k in range(6):
   p.emit('lb',10,18,k);p.emit('lb',11,19,k);multiply(p);p.emit('add',22,22,10)
 p.emit('sw',22,27,0);p.emit('lw',25,29,0)
 if custom:p.emit('RQNT8',24,22,25);relu(p,24);p.emit('sb',24,26,0)
 else:p.emit('addi',10,22,0);requant(p);relu(p,10);p.emit('sb',10,26,0)
 for reg,step in [(19,6),(28,4),(29,4),(27,4),(26,1)]:p.emit('addi',reg,reg,step)
 p.emit('addi',23,23,-1);p.emit('bne',23,0,'conv_channel');p.emit('addi',18,18,2)
 p.emit('addi',20,20,-1);p.emit('bne',20,0,'conv_position')

def dense(p,custom,chain):
 input_base=BASE+(0x1000 if chain else 0x100)
 p.li(19,BASE+0x180);p.li(28,BASE+0x200);p.li(29,BASE+0x210)
 p.li(26,BASE+0x1100);p.li(27,BASE+0x900);p.li(20,4)
 p.label('fc_neuron');p.li(18,input_base);p.emit('lw',22,28,0);p.li(23,6 if custom else 24)
 p.label('fc_inner')
 if custom:p.emit('lw',24,18,0);p.emit('lw',25,19,0);p.emit('DOT4ACC',22,24,25)
 else:p.emit('lb',10,18,0);p.emit('lb',11,19,0);multiply(p);p.emit('add',22,22,10)
 for reg in [18,19]:p.emit('addi',reg,reg,4 if custom else 1)
 p.emit('addi',23,23,-1);p.emit('bne',23,0,'fc_inner');p.emit('sw',22,27,0);p.emit('lw',25,29,0)
 if custom:p.emit('RQNT8',24,22,25);p.emit('sb',24,26,0)
 else:p.emit('addi',10,22,0);requant(p);p.emit('sb',10,26,0)
 for reg,step in [(28,4),(29,4),(26,1),(27,4)]:p.emit('addi',reg,reg,step)
 p.emit('addi',20,20,-1);p.emit('bne',20,0,'fc_neuron')
 # Same scale/zero-point for all four logits, first index wins ties.
 p.li(18,BASE+0x1100);p.emit('lb',22,18,0);p.li(24,0);p.li(20,1);p.li(23,4)
 p.label('argmax');p.emit('add',19,18,20);p.emit('lb',10,19,0);p.emit('bge',22,10,'argmax_skip')
 p.emit('addi',22,10,0);p.emit('addi',24,20,0);p.label('argmax_skip')
 p.emit('addi',20,20,1);p.emit('bne',20,23,'argmax');p.li(19,BASE+0x1110);p.emit('sw',24,19,0)

def fir(p,custom):
 p.li(24,BASE+0x300);p.li(26,BASE+0x1200);p.li(20,32)
 p.label('fir_output');p.emit('addi',18,24,0);p.li(19,BASE+0x380);p.li(22,0);p.li(23,8)
 p.label('fir_tap');p.emit('lh',10,18,0);p.emit('lh',11,19,0)
 if custom:p.emit('MAC16',22,10,11)
 else:multiply(p);p.emit('add',22,22,10)
 p.emit('addi',18,18,2);p.emit('addi',19,19,2);p.emit('addi',23,23,-1);p.emit('bne',23,0,'fir_tap')
 p.emit('srai',22,22,15);clip(p,22,16);p.emit('sw',22,26,0)
 p.emit('addi',24,24,2);p.emit('addi',26,26,4);p.emit('addi',20,20,-1);p.emit('bne',20,0,'fir_output')

def iir(p,custom):
 p.li(18,BASE+0x400);p.li(26,BASE+0x1300);p.li(20,32);p.li(24,0);p.li(8,8192);p.li(9,24576)
 p.label('iir_sample');p.li(22,0);p.emit('lh',10,18,0);p.emit('addi',11,8,0)
 if custom:p.emit('MAC16',22,10,11)
 else:multiply(p);p.emit('add',22,22,10)
 p.emit('addi',10,24,0);p.emit('addi',11,9,0)
 if custom:p.emit('MAC16',22,10,11)
 else:multiply(p);p.emit('add',22,22,10)
 p.emit('srai',22,22,15);clip(p,22,16);p.emit('addi',24,22,0);p.emit('sw',22,26,0)
 p.emit('addi',18,18,2);p.emit('addi',26,26,4);p.emit('addi',20,20,-1);p.emit('bne',20,0,'iir_sample')

def fft(p,custom):
 p.li(18,BASE+0x500);p.li(19,BASE+0x1400)
 for i in range(16):
  j=int(f'{i:04b}'[::-1],2)
  p.emit('lh',10,18,j*4);p.emit('lh',11,18,j*4+2);p.emit('sw',10,19,i*8);p.emit('sw',11,19,i*8+4)
 for m in [2,4,8,16]:
  t=f'fft{m}_';half=m//2;p.li(18,BASE+0x1400);p.li(23,16//m);p.label(t+'group')
  p.emit('addi',19,18,half*8);p.li(17,BASE+0x580);p.li(20,half);p.label(t+'butterfly')
  for rd,ptr,off,op in [(24,19,0,'lw'),(25,19,4,'lw'),(26,18,0,'lw'),(27,18,4,'lw'),(8,17,0,'lh'),(9,17,2,'lh')]:p.emit(op,rd,ptr,off)
  for source,coef,destination in [(24,8,28),(25,9,10),(24,9,29),(25,8,10)]:
   p.emit('addi',10,source,0);p.emit('addi',11,coef,0)
   if custom:p.emit('MUL16',10,10,11)
   else:multiply(p)
   if destination!=10:p.emit('addi',destination,10,0)
   elif coef==9:p.emit('sub',28,28,10);p.emit('srai',28,28,15)
   else:p.emit('add',29,29,10);p.emit('srai',29,29,15)
  p.emit('add',10,26,28);p.emit('add',11,27,29);p.emit('sub',12,26,28);p.emit('sub',13,27,29)
  for rd in [10,11,12,13]:p.emit('srai',rd,rd,1);clip(p,rd,16)
  for rd,ptr,off in [(10,18,0),(11,18,4),(12,19,0),(13,19,4)]:p.emit('sw',rd,ptr,off)
  p.emit('addi',18,18,8);p.emit('addi',19,19,8);p.emit('addi',17,17,(16//m)*4)
  p.emit('addi',20,20,-1);p.emit('bne',20,0,t+'butterfly')
  p.emit('addi',18,18,half*8);p.emit('addi',23,23,-1);p.emit('bne',23,0,t+'group')

CUSTOM_COUNTS={'CONV1D_INT8':72,'FC_INT8':28,'CHAIN_INT8':100,'FIR8_Q15':256,'IIR1_Q15':64,'FFT16_Q15':128}
def kernel(app,custom):
 p=Asm();p.li(21,BASE)
 if app in ['CONV1D_INT8','CHAIN_INT8']:conv(p,custom)
 if app in ['FC_INT8','CHAIN_INT8']:dense(p,custom,app=='CHAIN_INT8')
 if app=='FIR8_Q15':fir(p,custom)
 if app=='IIR1_Q15':iir(p,custom)
 if app=='FFT16_Q15':fft(p,custom)
 return p

def words(p):
 result=[]
 for i,ins in enumerate(p.ops):
  if ins[0] in ['beq','bne','blt','bge','bltu','bgeu']:
   off=p.offset(ins[3],i*4);assert off%4==0 and -4096<=off<=4094,(i,ins,off)
  if ins[0]=='jal':assert -1048576<=p.offset(ins[2],i*4)<=1048574
  result.append(p.encode(ins,i*4))
 assert len(result)<=4096,len(result)
 return result

def assembly(p):
 labels={v:k for k,v in p.labels.items()};lines=['.section .text','.globl _start','_start:']
 for i,ins in enumerate(p.ops):
  if i*4 in labels:lines.append(labels[i*4]+':')
  op,*a=ins
  if op in OPS:
   n=OPS[op];line=f'.insn r 0x0b, {n if n<4 else n-4}, {0 if n<4 else 1}, x{a[0]}, x{a[1]}, x{a[2]} # {op}'
  elif op in ['lb','lbu','lh','lw','sb','sh','sw']:line=f'{op} x{a[0]}, {a[2]}(x{a[1]})'
  elif op in ['beq','bne','blt','bge','bltu','bgeu']:line=f'{op} x{a[0]}, x{a[1]}, {a[2]}'
  elif op=='jal':line=f'jal x{a[0]}, {a[1]}'
  elif op=='jalr':line=f'jalr x{a[0]}, {a[2]}(x{a[1]})'
  elif op=='lui':line=f'lui x{a[0]}, 0x{a[1]:x}'
  elif op in ['ebreak','ecall']:line=op
  elif op in ['addi','andi','slli','srli','srai']:line=f'{op} x{a[0]}, x{a[1]}, {a[2]}'
  else:line=f'{op} '+', '.join(f'x{x}' for x in a)
  lines.append('    '+line)
 return '\n'.join(lines)+'\n'
