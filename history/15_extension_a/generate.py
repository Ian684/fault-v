from pathlib import Path
import random,json
from reference import OPS as CODES,execute
R=Path(__file__).resolve().parent
OPS=list(CODES)
rng=random.Random(0xa1618)
direct=json.loads((R/'programs/directed_vectors.json').read_text())
import build_custom
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

manifest=json.loads((R/'programs/demo_manifest.json').read_text())
(R/'programs/extension_manifest.json').write_text(json.dumps(dict(unit_vectors=len(unit),unit_reset_cancellations=26,unit_completed=len(unit)+26,ops=OPS,**manifest),indent=2))
print('Generated',len(unit),'unit reference vectors.')
