"""Instruction-word interpreter used to check generated programs before RTL runs."""
from reference import decode,execute
MASK=0xffffffff
def sx(v,w):return v-(1<<w) if v&(1<<(w-1)) else v
def run(words,initial,end_pc=None):
 regs=[0]*32;ram=bytearray(initial);pc=0;serial=[];status=0
 counts=dict(instructions=0,custom=0,loads=0,stores=0,extra=0)
 measured=True;total_custom=0
 for step in range(1000000):
  if end_pc is not None and pc==end_pc:measured=False
  if pc&3 or not 0<=pc//4<len(words):raise AssertionError(('fetch',hex(pc)))
  word=words[pc//4];opcode=word&127;rd=(word>>7)&31;f3=(word>>12)&7;rs1=(word>>15)&31;rs2=(word>>20)&31;f7=word>>25
  a,b=regs[rs1],regs[rs2];value=0;write=False;nxt=(pc+4)&MASK
  if word==0x00100073:return dict(ram=ram,status=status,uart=bytes(serial),counts=counts,total_custom=total_custom,halt_pc=pc,steps=step)
  if opcode==0x37:value=word&0xfffff000;write=True
  elif opcode==0x17:value=pc+(word&0xfffff000);write=True
  elif opcode==0x13:
   imm=sx(word>>20,12);shift=(word>>20)&31;write=True
   if f3==0:value=a+imm
   elif f3==1:value=a<<shift
   elif f3==2:value=int(sx(a,32)<imm)
   elif f3==3:value=int(a<(imm&MASK))
   elif f3==4:value=a^imm
   elif f3==5:value=sx(a,32)>>shift if f7==32 else a>>shift
   elif f3==6:value=a|imm
   elif f3==7:value=a&imm
   else:raise AssertionError('immediate')
  elif opcode==0x33:
   assert f7 in [0,32];write=True
   if f3==0:value=a-b if f7==32 else a+b
   elif f3==1:value=a<<(b&31)
   elif f3==2:value=int(sx(a,32)<sx(b,32))
   elif f3==3:value=int(a<b)
   elif f3==4:value=a^b
   elif f3==5:value=sx(a,32)>>(b&31) if f7==32 else a>>(b&31)
   elif f3==6:value=a|b
   elif f3==7:value=a&b
  elif opcode==0x0b:
   name,_,_,_=decode(word);value=execute(name,a,b,regs[rd]);write=True;total_custom+=1
   if measured:counts['custom']+=1;counts['extra']+=3 if name in ['DOT4ACC','MAC16','RQNT8','DOT8'] else 2
  elif opcode==0x63:
   imm=((word>>31)<<12)|(((word>>7)&1)<<11)|(((word>>25)&63)<<5)|(((word>>8)&15)<<1);imm=sx(imm,13)
   condition={0:a==b,1:a!=b,4:sx(a,32)<sx(b,32),5:sx(a,32)>=sx(b,32),6:a<b,7:a>=b}[f3]
   if condition:nxt=(pc+imm)&MASK
  elif opcode==0x6f:
   imm=((word>>31)<<20)|(((word>>12)&255)<<12)|(((word>>20)&1)<<11)|(((word>>21)&1023)<<1)
   value=pc+4;write=True;nxt=(pc+sx(imm,21))&MASK
  elif opcode==0x67:value=pc+4;write=True;nxt=((a+sx(word>>20,12))&MASK)&~1
  elif opcode in [0x03,0x23]:
   isstore=opcode==0x23
   imm=sx(((word>>25)<<5)|((word>>7)&31),12) if isstore else sx(word>>20,12)
   address=(a+imm)&MASK;size={0:1,1:2,2:4,4:1,5:2}[f3];assert address%size==0
   if 0x10000000<=address and address+size<=0x10004000:
    off=address-0x10000000
    if isstore:
     ram[off:off+size]=(b&((1<<(size*8))-1)).to_bytes(size,'little')
     if measured:counts['stores']+=1
    else:
     value=int.from_bytes(ram[off:off+size],'little');write=True
     if f3 in [0,1]:value=sx(value,size*8)
     if measured:counts['loads']+=1
   elif address in [0x20000000,0x20000100,0x20000104,0x20000200] and size==4:
    assert not measured,'MMIO in measured application'
    if isstore:
     if address==0x20000000:status=b
     if address==0x20000100:serial.append(b&255)
    else:value=1 if address==0x20000104 else 0;write=True
   else:raise AssertionError(('data',hex(pc),hex(address)))
  else:raise AssertionError(('instruction',hex(pc),hex(word)))
  if write and rd:regs[rd]=value&MASK
  regs[0]=0
  if measured:counts['instructions']+=1
  pc=nxt
 raise AssertionError('program timeout')
