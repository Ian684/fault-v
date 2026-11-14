import json
import random
from pathlib import Path
from reference import OPS, execute, encode, decode, step, pack8, soft_multiply

ROOT = Path(__file__).resolve().parent
count = 0
def check(ok):
    global count
    if not ok:
        raise AssertionError('Specification check {}'.format(count+1))
    count += 1

def oracle(op, a, b):
    aa, bb = a.to_bytes(4, 'little'), b.to_bytes(4, 'little')
    if op == 'DOT4':
        out = sum(int.from_bytes(aa[i:i+1], 'little', signed=True)*int.from_bytes(bb[i:i+1], 'little', signed=True) for i in range(4))
    elif op == 'MUL16':
        out = int.from_bytes(aa[:2], 'little', signed=True)*int.from_bytes(bb[:2], 'little', signed=True)
    elif op == 'ADDSAT':
        out = int.from_bytes(aa, 'little', signed=True)+int.from_bytes(bb, 'little', signed=True)
        if out > 2147483647: out = 2147483647
        if out < -2147483648: out = -2147483648
    else:
        out = int.from_bytes(aa, 'little', signed=True)//(2**(b % 32))
        if out > 127: out = 127
        if out < -128: out = -128
    return out % (2**32)

directed = [
 ('DOT4',0x04030201,0x08070605,70),
 ('DOT4',0x80808080,0x80808080,65536),
 ('DOT4',0x80808080,0x7f7f7f7f,0xffff0200),
 ('MUL16',0xffff8000,0x12348000,0x40000000),
 ('MUL16',0xabcdffff,2,0xfffffffe),
 ('ADDSAT',0x7fffffff,1,0x7fffffff),
 ('ADDSAT',0x80000000,0xffffffff,0x80000000),
 ('ADDSAT',0xffffffff,1,0),
 ('QNT8',0xfffffffd,1,0xfffffffe),
 ('QNT8',0x7fffffff,0,127),
 ('QNT8',0x80000000,0,0xffffff80),
 ('QNT8',0x80000000,31,0xffffffff),
 ('QNT8',256,33,127),
 ('QNT8',1,32,1),
]
for op,a,b,want in directed: check(execute(op,a,b)==want)
print('PASS directed semantics:',len(directed))
rng=random.Random(0xfa017)
for op in OPS:
    for _ in range(4096):
        a,b=rng.getrandbits(32),rng.getrandbits(32)
        check(execute(op,a,b)==oracle(op,a,b))
print('PASS independent random oracle: 16384 cases')
for op in OPS:
    for rd in range(32):
        for rs1 in range(32):
            for rs2 in range(32): check(decode(encode(op,rd,rs1,rs2))==(op,rd,rs1,rs2))
print('PASS encoding/decoding: 131072 register combinations')
for f7 in range(128):
    for f3 in range(8):
        inst=(f7<<25)|(f3<<12)|0x0b
        try: decode(inst);legal=True
        except ValueError: legal=False
        check(legal==(f7==0 and f3<4))
for opcode in range(128):
    try: decode(opcode);legal=True
    except ValueError: legal=False
    check(legal==(opcode==0x0b))
print('PASS legal/illegal function and opcode enumeration: 1152 cases')
for op in OPS:
    for rd,rs1,rs2 in [(3,1,2),(1,1,2),(2,1,2),(1,1,1),(0,1,2),(3,0,2),(3,1,0)]:
        regs=[0]*32;regs[1]=0x80808080;regs[2]=0x01010101
        old=regs[:];want=oracle(op,old[rs1],old[rs2]);step(encode(op,rd,rs1,rs2),regs)
        expected=old[:]
        if rd:expected[rd]=want
        check(regs==expected)
print('PASS architectural source/destination aliases and x0: 28 cases')

# Deterministic workloads: no measured cycles or speedups are inferred here.
a=[((i*37+11)%256)-128 for i in range(64)]
b=[((i*19+7)%256)-128 for i in range(64)]
dot=sum(soft_multiply(x,y,8) for x,y in zip(a,b))
dot_custom=sum(int.from_bytes(execute('DOT4',pack8(a[i:i+4]),pack8(b[i:i+4])).to_bytes(4,'little'),'little',signed=True) for i in range(0,64,4))
check(dot==dot_custom==sum(x*y for x,y in zip(a,b)))
samples=[((i*29+5)%256)-128 for i in range(23)]
coeff=[3,-2,1,4,-4,2,-1,3]
fir=[];quant=[]
for n in range(16):
    window=samples[n:n+8]
    baseline=sum(soft_multiply(x,y,8) for x,y in zip(window,coeff))
    custom=sum(int.from_bytes(execute('DOT4',pack8(window[i:i+4]),pack8(coeff[i:i+4])).to_bytes(4,'little'),'little',signed=True) for i in (0,4))
    check(baseline==custom==sum(x*y for x,y in zip(window,coeff)))
    fir.append(baseline)
    q=int.from_bytes(execute('QNT8',baseline&0xffffffff,3).to_bytes(4,'little'),'little',signed=True)
    check(q==min(127,max(-128,baseline//8)))
    quant.append(q)
samples16=[((i*7919+17)%65536)-32768 for i in range(23)]
coeff16=[300,-200,100,400,-400,200,-100,300]
fir16=[]
for n in range(16):
    terms=[execute('MUL16',x&0xffffffff,y&0xffffffff) for x,y in zip(samples16[n:n+8],coeff16)]
    custom=sum(int.from_bytes(t.to_bytes(4,'little'),'little',signed=True) for t in terms)
    baseline=sum(soft_multiply(x,y,16) for x,y in zip(samples16[n:n+8],coeff16))
    check(custom==baseline==sum(x*y for x,y in zip(samples16[n:n+8],coeff16)))
    check(-(1<<31)<=custom<(1<<31));fir16.append(custom)
sat_a=([2147483647,-2147483648,100,-100,0,2147483640,-2147483640,42]*8)
sat_b=([1,-1,-50,50,0,100,-100,-42]*8)
sat=[]
for x,y in zip(sat_a,sat_b):
    actual=execute('ADDSAT',x&0xffffffff,y&0xffffffff)
    expected=min(2147483647,max(-2147483648,x+y))&0xffffffff
    check(actual==expected);sat.append(expected)
bench={'dot64':{'a':a,'b':b,'expected':dot},'fir8':{'samples':samples,'coefficients':coeff,'definition':'sum samples[n+k]*coefficients[k], k=0..7; n=0..15','expected':fir,'qnt8_shift':3,'quantized':quant},'fir16':{'samples':samples16,'coefficients':coeff16,'expected':fir16},'satadd64':{'a':sat_a,'b':sat_b,'expected_u32':sat},'cycles':None,'speedup':None}
(ROOT/'benchmark_vectors.json').write_text(json.dumps(bench,indent=2),encoding='utf-8')
encoding={op:{'funct3':f,'match':hex((f<<12)|0x0b),'mask':'0xfe00707f','example_x5_x6_x7':hex(encode(op,5,6,7))} for op,f in OPS.items()}
(ROOT/'encoding.json').write_text(json.dumps(encoding,indent=2),encoding='utf-8')
vectors=[{'op':op,'a':hex(a),'b':hex(b),'expected':hex(want)} for op,a,b,want in directed]
(ROOT/'directed_vectors.json').write_text(json.dumps(vectors,indent=2),encoding='utf-8')
print('PASS benchmark mathematical equivalence: DOT64, FIR8+QNT8, FIR16, SATADD64')
print('DOT64 expected:',dot)
print('FIR8 expected:',fir)
print('FIR8 quantized:',quant)
print('ALL {} SPECIFICATION CHECKS PASSED'.format(count))
