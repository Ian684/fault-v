"""XFaultVDSP v1.1: mathematical semantics, independent of RTL structure."""
MASK=0xffffffff
OPS={name:i for i,name in enumerate(['DOT4', 'MUL16', 'ADDSAT', 'QNT8', 'DOT4ACC', 'MAC16', 'ADD8SAT', 'SUB8SAT', 'RQNT8', 'DOT2SAT', 'DOT8', 'DOT4SU'])}
def signed(v,w):
 v&=(1<<w)-1
 return v-(1<<w) if v>>(w-1) else v
def clamp(v,lo,hi):return min(hi,max(lo,v))
def execute(op,a,b,acc=0):
 a&=MASK;b&=MASK
 if op in ['DOT4','DOT4ACC','DOT4SU']:
  v=sum(signed(a>>(8*i),8)*(signed(b>>(8*i),8) if op!='DOT4SU' else ((b>>(8*i))&255)) for i in range(4))
  if op=='DOT4ACC':v+=acc
 elif op in ['MUL16','MAC16']:
  v=signed(a,16)*signed(b,16)
  if op=='MAC16':v+=acc
 elif op=='ADDSAT':v=clamp(signed(a,32)+signed(b,32),-2**31,2**31-1)
 elif op=='QNT8':v=clamp(signed(a,32)>>(b&31),-128,127)
 elif op in ['ADD8SAT','SUB8SAT']:
  v=sum((clamp(signed(a>>(8*i),8)+(1 if op=='ADD8SAT' else -1)*signed(b>>(8*i),8),-128,127)&255)<<(8*i) for i in range(4))
 elif op=='DOT2SAT':v=clamp(sum(signed(a>>(16*i),16)*signed(b>>(16*i),16) for i in range(2)),-2**31,2**31-1)
 elif op=='DOT8':v=sum(signed(a>>(4*i),4)*signed(b>>(4*i),4) for i in range(8))
 elif op=='RQNT8':
  product=signed(a,32)*signed(b,16);shift=(b>>16)&31;zp=signed(b>>21,8)
  # divmod implements nearest rounding with ties AWAY from zero.
  q,rem=divmod(abs(product),1<<shift)
  if shift and 2*rem>=(1<<shift):q+=1
  v=clamp((-q if product<0 else q)+zp,-128,127)
 else:raise ValueError(op)
 return v&MASK
def encode(op,rd,rs1,rs2):
 n=OPS[op]
 if any(not 0<=r<32 for r in [rd,rs1,rs2]):raise ValueError('register')
 f7,f3=(0,n) if n<4 else (1,n-4)
 return (f7<<25)|(rs2<<20)|(rs1<<15)|(f3<<12)|(rd<<7)|0x0b
def decode(word):
 f7,f3=word>>25,(word>>12)&7
 if word&127!=11 or not ((f7==0 and f3<4) or f7==1):raise ValueError('encoding')
 n=f3 if f7==0 else f3+4
 return list(OPS)[n],(word>>7)&31,(word>>15)&31,(word>>20)&31
def pack8(v):return sum((x&255)<<(8*i) for i,x in enumerate(v))
def step(inst,regs):
 op,d,a,b=decode(inst);v=execute(op,regs[a] if a else 0,regs[b] if b else 0,regs[d] if d else 0)
 if d:regs[d]=v
 regs[0]=0
 return v
