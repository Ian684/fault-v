from pathlib import Path
import json,random,shutil

R=Path(__file__).resolve().parent
OPS=['DOT4','MUL16','ADDSAT','QNT8','DOT4ACC','MAC16','ADD8SAT','SUB8SAT','RQNT8','DOT2SAT','DOT8','DOT4SU']
reference='''"""XFaultVDSP v1.1: mathematical semantics, independent of RTL structure."""
MASK=0xffffffff
OPS={name:i for i,name in enumerate(%r)}
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
''' % OPS
(R/'reference.py').write_text(reference)
from reference import execute,encode
rng=random.Random(0xa1618)
old=json.loads((R/'programs/directed_vectors.json').read_text())[:14]
new={
 'DOT4ACC':[(0x80808080,0x80808080),(0x04030201,0x08070605),(0xffffffff,0x01010101),(0,0)],
 'MAC16':[(0x8000,0x8000),(0xffff,0x7fff),(0x1234ffff,0x9876ffff),(0,0)],
 'ADD8SAT':[(0x7f7f7f7f,0x01010101),(0x80808080,0xffffffff),(0x7f8001ff,0x01807f01),(0,0)],
 'SUB8SAT':[(0x7f7f7f7f,0xffffffff),(0x80808080,0x01010101),(0x7f8001ff,0x807f0180),(0,0)],
 'RQNT8':[(0x80000000,0x7fff),(0x7fffffff,0x8000),(-3,(1<<16)|1),(3,(((-4)&255)<<21)|(1<<16)|1)],
 'DOT2SAT':[(0x80008000,0x80008000),(0x7fff7fff,0x7fff7fff),(0x80008000,0x7fff7fff),(0,0)],
 'DOT8':[(0x88888888,0x88888888),(0x88888888,0x77777777),(0xfedcba98,0x01234567),(0,0)],
 'DOT4SU':[(0x80808080,0xffffffff),(0x7f7f7f7f,0xffffffff),(0xff01807f,0xffff8080),(0,0)]}
direct=old.copy()
for op,pairs in new.items():
 for a,b in pairs:direct.append(dict(op=op,a=f'{a&0xffffffff:08x}',b=f'{b:08x}',expected=f'{execute(op,a,b):08x}'))
(R/'programs/directed_vectors.json').write_text(json.dumps(direct,indent=2))

# Adapt deterministic CPU trace generator to old-rd semantics and enlarged encoding space.
p=R/'build_custom.py';s=p.read_text()
s=s.replace('execute(op,regs[a[1]],regs[a[2]])','execute(op,regs[a[1]],regs[a[2]],regs[rd])')
s=s.replace('p=CustomProgram();p.li(1,a);p.li(2,b)','p=CustomProgram();p.li(1,a);p.li(2,b)\n    if rd not in [0,1,2]:p.li(rd,0x7ffffffe)')
s=s.replace('if f7==0 and f3<4:continue','if (f7==0 and f3<4) or f7==1:continue')
s=s.replace("s=f'.insn r 0x0b, {OPS[op]}, 0, x{a[0]}, x{a[1]}, x{a[2]} # {op}'", "s=f'.insn r 0x0b, {OPS[op] if OPS[op]<4 else OPS[op]-4}, {0 if OPS[op]<4 else 1}, x{a[0]}, x{a[1]}, x{a[2]} # {op}'")
# Explicitly initialize old rd for self-check accumulator instructions.
s=s.replace("p.li(1,int(v['a'],16));p.li(2,int(v['b'],16));p.emit(v['op'],5,1,2)","p.li(1,int(v['a'],16));p.li(2,int(v['b'],16));p.li(5,0);p.emit(v['op'],5,1,2)")
p.write_text(s)
import build_custom
manifest=json.loads((R/'programs/demo_manifest.json').read_text())

unit=[]
for row in direct:
 op=OPS.index(row['op']);a=int(row['a'],16);b=int(row['b'],16)
 unit.append((op,a,b,0,execute(row['op'],a,b)))
for op,name in enumerate(OPS):
 for _ in range(4096):
  a,b,acc=(rng.getrandbits(32) for _ in range(3))
  unit.append((op,a,b,acc,execute(name,a,b,acc)))
# Exhaust every pair of INT8 lane operands for ADD/SUB saturation.
for op in [6,7]:
 for a in range(256):
  for b in range(256):
   av=a*0x01010101;bv=b*0x01010101
   unit.append((op,av,bv,0,execute(OPS[op],av,bv)))
# Shift extremes, exact ties, zero points, 48-bit products and ignored upper controls.
for a in [-2**31,-65537,-65536,-32769,-32768,-257,-129,-3,-1,0,1,3,127,128,32767,32768,65535,65536,2**31-1]:
 for mult in [-32768,-32767,-1,0,1,3,32767]:
  for shift in range(32):
   for zp in [-128,-1,0,1,127]:
    b=(mult&65535)|(shift<<16)|((zp&255)<<21)|(rng.randrange(8)<<29)
    unit.append((8,a&0xffffffff,b,0,execute('RQNT8',a,b)))
(R/'verify/unit.vec').write_text(str(len(unit))+'\n'+''.join(f'{o} {a:08x} {b:08x} {c:08x} {v:08x}\n' for o,a,b,c,v in unit))

p=R/'verify/tb_custom_exec.sv';s=p.read_text().replace('req_a=0,req_b=0,rsp_result','req_a=0,req_b=0,req_acc=0,rsp_result')
s=s.replace('input logic [31:0] a,b,want','input logic [31:0] a,b,acc,want').replace('req_b=b;req_valid','req_b=b;req_acc=acc;req_valid')
s=s.replace('req_b=~b;req_op','req_b=~b;req_acc=~acc;req_op').replace('(op==0?4:1)','((op==8 || op==10)?2:1)')
s=s.replace('70,2);','0,70,2);').replace('logic [31:0] av,bv,expected;','logic [31:0] av,bv,cv,expected;')
s=s.replace('"%d %h %h %h",op,av,bv,expected','"%d %h %h %h %h",op,av,bv,cv,expected').replace('scanned==4','scanned==5').replace('operation(op,av,bv,expected','operation(op,av,bv,cv,expected')
s=s.replace('for(integer c=0;c<=4;c++)cancel(0,c);\n        for(integer k=1;k<4;k++)begin cancel(k,0);cancel(k,1);end','for(integer k=0;k<12;k++)for(integer c=0;c<=((k==8 || k==10)?2:1);c++)cancel(k,c);')
s=s.replace('#10000000','#500000000');p.write_text(s)
p=R/'verify/tb_custom_cpu.sv';s=p.read_text().replace('ST_CUSTOM_START,ST_CUSTOM_WAIT,ST_CUSTOM_COMMIT','ST_CUSTOM_ACC_READ,ST_CUSTOM_START,ST_CUSTOM_WAIT,ST_CUSTOM_COMMIT')
s=s.replace('ALL 2638 CUSTOM CPU CASE RUNS PASSED',f'ALL {manifest["cpu_cases_per_mode"]*2} CUSTOM CPU CASE RUNS PASSED');p.write_text(s)
p=R/'run_custom.ps1';s=p.read_text().replace('ALL 2638 CUSTOM CPU CASE RUNS PASSED',f'ALL {manifest["cpu_cases_per_mode"]*2} CUSTOM CPU CASE RUNS PASSED').replace('ALL 7 CUSTOM CPU RESET STAGES PASSED','ALL 52 CUSTOM CPU RESET STAGES PASSED');p.write_text(s)
p=R/'verify/tb_custom_program.sv';s=p.read_text().replace('customs==270',f'customs=={manifest["custom_instructions"]}').replace('count==127',f'count=={manifest["stored_outputs"]}');p.write_text(s)

# Reuse original paired workloads with unchanged measured boundaries.
for name in ['build_benchmarks.py','run_benchmark.ps1']:
 shutil.copy2(R.parent/'benchmark'/name,R/name)
shutil.copy2(R.parent/'benchmark/verify/tb_benchmark.sv',R/'verify/tb_benchmark.sv')
p=R/'create_project.tcl';s=p.read_text().replace('fault_v_custom','fault_v_extension_a');p.write_text(s)
p=R/'build.tcl';s=p.read_text().replace('fault_v_custom','fault_v_extension_a').replace('[llength $dsps] != 1','[llength $dsps] != 4').replace('Expected exactly one shared multiplier DSP','Expected four parallel multiplier DSPs').replace('CUSTOM FPGA BUILD PASSED','EXTENSION A FPGA BUILD PASSED');p.write_text(s)
p=R/'run_build.ps1';s=p.read_text().replace('CUSTOM FPGA BUILD PASSED','EXTENSION A FPGA BUILD PASSED');p.write_text(s)
(R/'programs/extension_manifest.json').write_text(json.dumps(dict(unit_vectors=len(unit),unit_reset_cancellations=26,unit_completed=len(unit)+26,ops=OPS,**manifest),indent=2))
print('Prepared extension:',len(unit),'unit vectors,',manifest)
