"""Regenerate deterministic CPU programs and custom-unit reference vectors."""
from pathlib import Path
import json,random
from reference import OPS,execute
import build_custom

root=Path(__file__).resolve().parent
cases=[]
for v in json.loads((root/'programs/directed_vectors.json').read_text()):
    cases.append((OPS[v['op']],int(v['a'],16),int(v['b'],16),int(v['expected'],16)))
rng=random.Random(0x1718)
for name,op in OPS.items():
    for _ in range(4096):
        a,b=rng.getrandbits(32),rng.getrandbits(32)
        cases.append((op,a,b,execute(name,a,b)))
(root/'verify/unit.vec').write_text(str(len(cases))+'\n'+''.join(f'{op} {a:08x} {b:08x} {w:08x}\n' for op,a,b,w in cases))
print('Generated {} custom unit reference vectors'.format(len(cases)))
