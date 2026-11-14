"""Add GDS-extracted antenna areas without changing a single LEF geometry line."""
from pathlib import Path
from functools import lru_cache
from collections import Counter
from decimal import Decimal
import hashlib, json, re

R = Path(__file__).resolve().parents[1]
name = 'sky130_sram_2kbyte_1rw1r_32x512_8'
out = R / 'reports/antenna_model'
original = R / f'macros/{name}.lef'
gds = R / f'macros/{name}.gds'
sp = R.parent / f'design/macros/vendor/{name}.sp'
if not sp.exists():
    sp = R / f'macros/{name}.source.sp'
raw = out / 'sram_gds_antenna.lef'

def pins(text):
    return {m[1]: m[2] for m in re.finditer(r'\bPIN\s+(\S+)(.*?)\n\s+END\s+\1(?=\s)', text, re.S)}

base = pins(original.read_text())
extracted = pins(raw.read_text())
assert set(base) == set(extracted) and len(base) == 125
areas = {}
for pin, body in base.items():
    direction = re.search(r'DIRECTION\s+(\w+)', body)[1]
    kind = 'GATE' if direction == 'INPUT' else 'DIFF'
    if direction not in ('INPUT', 'OUTPUT'):
        continue
    values = re.findall(r'ANTENNA' + kind + r'AREA\s+([\d.]+)\s*;', extracted[pin])
    assert len(values) == 1 and Decimal(values[0]) > 0, (pin, values)
    areas[pin] = {kind.lower() + '_area_um2': values[0]}
assert Counter('gate' if 'gate_area_um2' in x else 'diff' for x in areas.values()) == {'gate': 59, 'diff': 64}

# Independent connectivity/width/length calculation from the supplied untrimmed SPICE.
subckts = {}
current = None
for line in sp.read_text().splitlines():
    tok = line.split()
    if not tok or tok[0].startswith('*'):
        continue
    if tok[0].lower() == '.subckt':
        current = tok[1]
        subckts[current] = (tok[2:], [])
    elif tok[0].lower() == '.ends':
        current = None
    elif current and tok[0][0].lower() == 'x':
        subckts[current][1].append(tok)

@lru_cache(None)
def gate_areas(cell):
    ports, instances = subckts[cell]
    total = {p: Decimal(0) for p in ports}
    for tok in instances:
        split = next((i for i, t in enumerate(tok) if '=' in t), len(tok))
        model, nets = tok[split - 1], tok[1:split - 1]
        if model in subckts:
            child_ports, _ = subckts[model]
            assert len(nets) == len(child_ports), (cell, tok[0], model)
            child = gate_areas(model)
            for formal, net in zip(child_ports, nets):
                if net in total:
                    total[net] += child[formal]
        else:
            assert model.startswith('sky130_fd_pr__') and len(nets) == 4, (cell, tok)
            params = dict(t.lower().split('=', 1) for t in tok[split:])
            assert {'w', 'l'} <= params.keys(), (cell, tok)
            if nets[1] in total:
                assert set(params) <= {'w', 'l', 'm', 'pd', 'ps', 'as', 'ad'}, params
                total[nets[1]] += Decimal(params['w']) * Decimal(params['l']) * Decimal(params.get('m', '1'))
    return total

independent = gate_areas(name)
comparison = {}
for pin, values in areas.items():
    if 'gate_area_um2' in values:
        measured = Decimal(values['gate_area_um2'])
        expected = independent[pin]
        comparison[pin] = {'GDS_um2': str(measured), 'SPICE_um2': str(expected)}
        assert abs(measured - expected) <= Decimal('0.000001'), (pin, measured, expected)

text = original.read_text()
for pin, values in areas.items():
    kind, value = next(iter(values.items()))
    keyword = 'ANTENNAGATEAREA' if kind == 'gate_area_um2' else 'ANTENNADIFFAREA'
    pattern = r'(\bPIN\s+' + re.escape(pin) + r'\s*\n\s+DIRECTION\s+\w+\s*;)'
    text, n = re.subn(pattern, lambda m: m[1] + f'\n      {keyword} {value} ;', text)
    assert n == 1
strip = lambda s: re.sub(r'^\s*ANTENNA(?:GATE|DIFF)AREA[^\n]*\n', '', s, flags=re.M)
assert strip(text) == original.read_text()
target = R / f'macros/{name}.antenna.lef'
assert not target.exists()
target.write_text(text)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receipt = {'pass': True, 'scope': 'Top-level routed LEF antenna model; not SRAM internal foundry antenna signoff',
           'method': 'Magic 8.3.623 from exact GDS; all 59 gate areas independently equal hierarchical SPICE W*L sums; diffusion areas from physical GDS only',
           'geometry_and_pin_directions_unchanged': True, 'gate_pins': 59, 'diffusion_pins': 64,
           'files_sha256': {str(p.relative_to(R.parent)): sha(p) for p in [original, gds, sp, raw, target]},
           'pin_areas': areas, 'independent_gate_comparison': comparison}
(out / 'sram_antenna_model.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ['pin_areas','independent_gate_comparison']}, indent=2))
