"""H1 PG via4 EM repair (openroad -python), H0 method (week25_closure prepare_pg_via_trial.py + local DRC acceptance as in
trial_compact_pg_intersections.py). Input: routed H1 candidate (before fill). Selection: native PDNSim 28 mW/SRAM branch
current per via4 cut > 1.2 mA (H0 selection threshold). Each selected via becomes a real multi-cut array whose M4 landing lies
wholly inside existing same-net M4 (PDN strap or SRAM pin), whose M5 enclosure is >= 1.6 um from opposite-net M5, and whose
placement adds no native DRC marker in a local window. Only PG via shapes change; cells, signal wires, guides unchanged.
Env: SRC_ODB, EM_DIR (IR run step dir with em-VPWR.csv / em-VGND.csv), OUT_DIR."""
import csv, hashlib, json, math, os, re, sys
from collections import Counter
from pathlib import Path
import odb
from openroad import Tech, Design
sys.path.insert(0, '/work/routing/scripts')
from temporary_fixed_routes import fixed, wires, guides, obstructions

SRC = Path(os.environ['SRC_ODB']); EM = Path(os.environ['EM_DIR']); OUT = Path(os.environ['OUT_DIR'])
OUT.mkdir(parents=True, exist_ok=False)
THRESHOLD_A = 0.0012
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
t = Tech(); design = Design(t); design.readDb(str(SRC)); db = design.getDb(); b = db.getChip().getBlock()
assert b.getDbUnitsPerMicron() == 1000
design.evalTclString('set_thread_count 4')
before = fixed(b); old_wires = wires(b); old_guides = guides(b); old_obs = obstructions(b)
rect = lambda q: (q.xMin(), q.yMin(), q.xMax(), q.yMax())
contains = lambda a, z: a[0] <= z[0] and a[1] <= z[1] and a[2] >= z[2] and a[3] >= z[3]
distance = lambda a, z: math.hypot(max(a[0] - z[2], z[0] - a[2], 0), max(a[1] - z[3], z[1] - a[3], 0))

support = {n: {'met4': [], 'met5': []} for n in ('VPWR', 'VGND')}; physical = {}; swires = {}
for name in support:
    for sw in b.findNet(name).getSWires():
        for q in sw.getWires():
            if not q.isVia():
                layer = q.getTechLayer().getName()
                if layer in support[name]: support[name][layer].append(rect(q))
                continue
            via = q.getBlockVia() or q.getTechVia()
            if any(z.getTechLayer().getName() == 'via4' for z in via.getBoxes()):
                key = (name, *q.getViaXY()); assert key not in physical, key
                physical[key] = q; swires[key] = sw
    for i in b.getInsts():
        if not i.getMaster().isBlock(): continue
        for p in i.getITerms():
            if p.getNet() is None or p.getNet().getName() != name: continue
            for layer, z in p.getGeometries():
                if layer.getName() in support[name]: support[name][layer.getName()].append(rect(z))

# ---- native branch currents (28 mW/SRAM run) -> physical via4 ----
currents = {}; unmapped = []
for name in ('VPWR', 'VGND'):
    with open(EM / f'em-{name}.csv', newline='') as f:
        for row in csv.DictReader(f):
            layers = {row['Node0 Layer'], row['Node1 Layer']}
            if layers != {'met4', 'met5'}: continue
            pts = {(round(float(row[f'Node{i} X location']) * 1000), round(float(row[f'Node{i} Y location']) * 1000)) for i in (0, 1)}
            cur = abs(float(row['Current']))
            hits = [(name, *xy) for xy in pts if (name, *xy) in physical]
            if not hits:
                hits = [k for k in physical if k[0] == name and any(rect(physical[k])[0] <= x <= rect(physical[k])[2] and rect(physical[k])[1] <= y <= rect(physical[k])[3] for x, y in pts)]
            if len(hits) != 1:
                unmapped.append({'net': name, 'points': sorted(pts), 'current_A': cur, 'candidates': [list(h) for h in hits]}); continue
            currents[hits[0]] = currents.get(hits[0], 0) + cur

selected = []
for key, cur in sorted(currents.items()):
    old = physical[key].getBlockVia() or physical[key].getTechVia()
    cuts = sum(z.getTechLayer().getName() == 'via4' for z in old.getBoxes())
    if cur / cuts > THRESHOLD_A: selected.append((key, cur, cuts))
required_unmapped = [u for u in unmapped if u['current_A'] > THRESHOLD_A]
print('PG_SELECTION', len(selected), 'unmapped', len(unmapped), 'unmapped above threshold', len(required_unmapped), flush=True)


def drc(box, tag):
    design.getTritonRoute().clearDesign(); p = OUT / f'{tag}.rpt'
    design.evalTclString(f'drt::check_drc -box {{{" ".join(map(str, box))}}} -output_file {p} -marker_name PGH1')
    text = p.read_text(); rows = re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)', text)
    assert len(rows) == text.count('violation type:'); p.unlink(); return Counter(rows)


props = ('BottomLayer', 'CutLayer', 'TopLayer', 'NumCutCols', 'NumCutRows', 'XCutSize', 'YCutSize', 'XCutSpacing', 'YCutSpacing',
         'XOrigin', 'YOrigin', 'XBottomEnclosure', 'YBottomEnclosure', 'XTopEnclosure', 'YTopEnclosure', 'XBottomOffset',
         'YBottomOffset', 'XTopOffset', 'YTopOffset')
masters = {}; planned = []; failed = []
for idx, (key, cur, old_cuts) in enumerate(selected):
    name, x, y = key; opposite = 'VGND' if name == 'VPWR' else 'VPWR'
    box = physical[key]; old = box.getBlockVia(); assert old is not None and old.hasParams()
    p0 = old.getViaParams(); assert p0.getXCutSize() == p0.getYCutSize() == 800 and p0.getXCutSpacing() == p0.getYCutSpacing() == 800
    top = next(rect(q) for q in old.getBoxes() if q.getTechLayer().getName() == 'met5')
    old_top = (x + top[0], y + top[1], x + top[2], y + top[3])
    win = [x - 25000, y - 25000, x + 25000, y + 25000]
    baseline = drc(win, f'{idx}_base'); accepted = None; tried = []
    shapes = [(2, 4), (1, 8), (4, 2), (8, 1), (2, 2), (1, 4), (4, 1)]
    for cols, rows in shapes:
        if cur / (cols * rows) > THRESHOLD_A: continue
        cw, ch = 800 * cols + 800 * (cols - 1), 800 * rows + 800 * (rows - 1)
        bx, by = 190, 190; tx, ty = max(310, (1600 - cw) // 2), max(310, (1600 - ch) // 2)
        bw, bh, tw, th = cw + 2 * bx, ch + 2 * by, cw + 2 * tx, ch + 2 * ty
        centers = [(x, y), (x, old_top[3] - th // 2), (x, old_top[1] + th // 2), (old_top[2] - tw // 2, y), (old_top[0] + tw // 2, y)]
        for nx, ny in centers:
            bottom = (nx - bw // 2, ny - bh // 2, nx + bw // 2, ny + bh // 2); upper = (nx - tw // 2, ny - th // 2, nx + tw // 2, ny + th // 2)
            if not any(contains(z, bottom) for z in support[name]['met4']): continue
            if any(distance(z, upper) < 1600 for z in support[opposite]['met5']): continue
            sig = (cols, rows, bx, by, tx, ty)
            if sig not in masters:
                v = odb.dbVia.create(b, 'H1_PG_VIA4_' + '_'.join(map(str, sig))); params = odb.dbViaParams()
                for prop in props: getattr(params, 'set' + prop)(getattr(p0, 'get' + prop)())
                params.setNumCutCols(cols); params.setNumCutRows(rows)
                for prop, val in zip(('XBottomEnclosure', 'YBottomEnclosure', 'XTopEnclosure', 'YTopEnclosure'), (bx, by, tx, ty)): getattr(params, 'set' + prop)(val)
                v.setViaGenerateRule(old.getViaGenerateRule()); v.setViaParams(params)
                assert sum(q.getTechLayer().getName() == 'via4' for q in v.getBoxes()) == cols * rows
                masters[sig] = v
            shape = str(box.getWireShapeType()); oldxy = (x, y)
            odb.dbSBox.destroy(box); new = odb.dbSBox.create(swires[key], masters[sig], nx, ny, shape); assert new
            observed = drc(win, f'{idx}_try'); ok = not (observed - baseline)
            tried.append({'cols': cols, 'rows': rows, 'xy': [nx, ny], 'new_markers': sum((observed - baseline).values())})
            if ok:
                accepted = {'net': name, 'old_xy': [x, y], 'old_via': old.getName(), 'old_cut_count': old_cuts, 'current_28mW_A': cur,
                            'new_xy': [nx, ny], 'new_via': masters[sig].getName(), 'cuts': cols * rows, 'cols': cols, 'rows': rows,
                            'new_bottom_box': bottom, 'new_top_box': upper, 'new_bbox': rect(new), 'local_markers_before': sum(baseline.values()),
                            'local_markers_after': sum(observed.values())}
                physical[key] = new; support[name]['met5'].append(upper); break
            odb.dbSBox.destroy(new); box = odb.dbSBox.create(swires[key], old, *oldxy, shape); assert box; physical[key] = box
        if accepted: break
    if accepted: planned.append(accepted)
    else: failed.append({'net': name, 'old_xy': [x, y], 'current_28mW_A': cur, 'tried': tried})
    print('PG_SITE', idx, name, x, y, round(cur * 1000, 3), 'mA', 'accepted' if accepted else 'FAILED', accepted and (accepted['cols'], accepted['rows']), flush=True)

after = fixed(b)
assert after[:2] == before[:2] and wires(b) == old_wires and guides(b) == old_guides and obstructions(b) == old_obs
out_odb = OUT / 'fault_v_asic_top.odb'; odb.write_db(db, str(out_odb))
record = {'source_ODB_sha256': sha(SRC), 'output_ODB_sha256': sha(out_odb), 'selection_threshold_A_per_cut_28mW': THRESHOLD_A,
          'selected': len(selected), 'replaced': len(planned), 'failed': failed, 'unmapped_branches': unmapped,
          'unmapped_above_threshold': required_unmapped, 'total_new_cuts': sum(r['cuts'] for r in planned),
          'cut_shapes': dict(Counter(f"{r['cols']}x{r['rows']}" for r in planned)), 'replacements': planned,
          'all_cells_graph_signal_wires_guides_obstructions_unchanged': True,
          'scope': 'PG via4 shapes only (H0 PG_B/PG_G method on H1). Full-chip native DRC, full-GDS KLayout DRC, core LVS, PG contact audit, fresh IR/EM, antenna, STA and fill must be rerun on this candidate.'}
(OUT / 'pg_h1_fix.json').write_text(json.dumps(record, indent=2) + '\n')
print('PG_H1_FIX_DONE replaced', len(planned), 'failed', len(failed), 'cuts', record['total_new_cuts'], record['output_ODB_sha256'], flush=True)
