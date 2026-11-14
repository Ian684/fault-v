"""H1 version of week25_signoff/scripts/inspect_pdn.py (openroad -python): voltage sources on existing met5 PG terminals
within 100 um of the die edge (same rule, H1 die size). Writes controls/VPWR.loc, controls/VGND.loc, reports/PDN_boundary.json."""
from pathlib import Path
import json
import odb

w = Path('/work/ppa/h1/cand_gap90x95/closure_c')
db = odb.dbDatabase.create()
odb.read_db(db, '/work/ppa/h1/cand_gap90x95/runs/h1c_post/1-openroad-fillinsertion/fault_v_asic_top.odb')
block = db.getChip().getBlock()
units = block.getDbUnitsPerMicron()
die = block.getDieArea()
W, H = die.xMax() / units, die.yMax() / units
assert (W, H) == (2470, 3217), (W, H)
edge = lambda x, y: x < 100 or x > W - 100 or y < 100 or y > H - 100
result = {'db_units_per_um': units, 'die_um': [W, H], 'rule': 'met5 PG terminal points within 100 um of the die edge', 'ports': {}, 'sources': {}}
for name in ('VPWR', 'VGND'):
    bt = block.findBTerm(name)
    assert bt is not None
    boxes = [box for pin in bt.getBPins() for box in pin.getBoxes()]
    result['ports'][name] = [{'layer': b.getTechLayer().getName(), 'box_um': [v / units for v in (b.xMin(), b.yMin(), b.xMax(), b.yMax())]} for b in boxes]
    top = [b for b in boxes if b.getTechLayer().getName() == 'met5']
    assert top, 'No existing top-metal PG terminals'
    sources = []
    for b in top:
        x0, y0, x1, y1 = [v / units for v in (b.xMin(), b.yMin(), b.xMax(), b.yMax())]
        coords = [((x0 + x1) / 2, y0 + 10), ((x0 + x1) / 2, y1 - 10)] if y1 - y0 > x1 - x0 else [(x0 + 10, (y0 + y1) / 2), (x1 - 10, (y0 + y1) / 2)]
        sources += [[x, y, min(x1 - x0, y1 - y0), 1.8 if name == 'VPWR' else 0] for x, y in coords if edge(x, y)]
    sources = [list(r) for r in sorted(set(tuple(round(v, 6) for v in s) for s in sources))]
    assert sources and all(edge(x, y) for x, y, _, _ in sources)
    result['sources'][name] = sources
    (w / f'controls/{name}.loc').write_text(''.join(','.join(map(str, s)) + '\n' for s in sources))
result['macro_instances'] = [i.getName() for i in block.getInsts() if i.getMaster().isBlock()]
assert len(result['macro_instances']) == 18
(w / 'reports/PDN_boundary.json').write_text(json.dumps(result, indent=2) + '\n')
print('PDN_BOUNDARY', {k: len(v) for k, v in result['sources'].items()})
