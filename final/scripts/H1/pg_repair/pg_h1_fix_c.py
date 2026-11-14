"""H1 PG repair pass c (openroad -python), H0 PG_C/PG_D method (week25_closure prepare_pg_c_plan.py): at every site that
still violates average EM in the pass-b screen, widen the existing 1.74 um M4 rail to 2.8 um with a same-net M4 patch that
covers the array landing and the violating M4 run, and replace the site's via4 array with a 2-column array (2x4 up to
9.6 mA, 2x6 up to 14.4 mA, else 2x8) aligned to the M5 strap edge on the side the current flows. Each site is accepted only
if a local native DRC window shows no new marker; otherwise the site is restored and reported.
Env: SRC_ODB (pass-b output), SCREEN_JSON (screen EM audit of SRC_ODB), PASS_A_JSON, PASS_B_JSON, OUT_DIR."""
import hashlib, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path
import odb
from openroad import Tech, Design
sys.path.insert(0, '/work/routing/scripts')
from temporary_fixed_routes import fixed, wires, guides, obstructions

SRC = Path(os.environ['SRC_ODB']); OUT = Path(os.environ['OUT_DIR']); OUT.mkdir(parents=True, exist_ok=False)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
screen = json.loads(Path(os.environ['SCREEN_JSON']).read_text())
pa = json.loads(Path(os.environ['PASS_A_JSON']).read_text()); pb = json.loads(Path(os.environ['PASS_B_JSON']).read_text())
assert pb['output_ODB_sha256'] == sha(SRC)
t = Tech(); design = Design(t); design.readDb(str(SRC)); db = design.getDb(); b = db.getChip().getBlock(); tech = db.getTech()
design.evalTclString('set_thread_count 4')
before = fixed(b); old_wires = wires(b); old_guides = guides(b); old_obs = obstructions(b)
rect = lambda q: (q.xMin(), q.yMin(), q.xMax(), q.yMax())
contains = lambda a, z: a[0] <= z[0] and a[1] <= z[1] and a[2] >= z[2] and a[3] >= z[3]
import math
distance = lambda a, z: math.hypot(max(a[0] - z[2], z[0] - a[2], 0), max(a[1] - z[3], z[1] - a[3], 0))

# repaired sites from passes a/b: original single-cut via xy -> current array xy, pre-repair current
sites = {}
for r in pa['replacements'] + pb['replacements']:
    sites[(r['net'], *r['old_xy'])] = {'array_xy': tuple(r['new_xy']), 'current_A': r['current_28mW_A'], 'old_bbox': None}
for r in pa['failed']:
    if (r['net'], *r['old_xy']) not in sites:
        sites[(r['net'], *r['old_xy'])] = {'array_xy': tuple(r['old_xy']), 'current_A': r['current_28mW_A'], 'old_bbox': None}

# group screen violations to their site: same net, M4 node x == site x, nearest strap y within 40 um
hot = defaultdict(list)
for v in screen['violations']:
    m4 = [n for n in (v['node0'], v['node1']) if n[0] == 'met4']
    x = m4[0][1]; ys = [n[2] for n in m4]
    cands = [k for k in sites if k[0] == v['net'] and abs(k[1] - x) <= 2000 and min(abs(k[2] - y) for y in ys) <= 40000]
    assert cands, v
    k = min(cands, key=lambda k: min(abs(k[2] - y) for y in ys))
    hot[k].append(v)
print('PG_C_SITES', len(hot), flush=True)


def drc(box, tag):
    design.getTritonRoute().clearDesign(); p = OUT / f'{tag}.rpt'
    design.evalTclString(f'drt::check_drc -box {{{" ".join(map(str, box))}}} -output_file {p} -marker_name PGH1C')
    text = p.read_text(); rows = re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)', text)
    assert len(rows) == text.count('violation type:'); p.unlink(); return Counter(rows)


props = ('BottomLayer', 'CutLayer', 'TopLayer', 'NumCutCols', 'NumCutRows', 'XCutSize', 'YCutSize', 'XCutSpacing', 'YCutSpacing',
         'XOrigin', 'YOrigin', 'XBottomEnclosure', 'YBottomEnclosure', 'XTopEnclosure', 'YTopEnclosure', 'XBottomOffset',
         'YBottomOffset', 'XTopOffset', 'YTopOffset')
met4 = tech.findLayer('met4'); accepted = []; failed = []
for idx, (key, viol) in enumerate(sorted(hot.items())):
    net, x0, y0 = key; opposite = 'VGND' if net == 'VPWR' else 'VPWR'; site = sites[key]; cur = site['current_A']
    n = b.findNet(net)
    # the site's present via4 shape (array from pass a/b, or the original single cut)
    found = [(sw, q) for sw in n.getSWires() for q in sw.getWires() if q.isVia() and tuple(q.getViaXY()) == site['array_xy']
             and any(z.getTechLayer().getName() == 'via4' for z in (q.getBlockVia() or q.getTechVia()).getBoxes())]
    assert len(found) == 1, (key, len(found)); sw, box = found[0]; oldvia = box.getBlockVia() or box.getTechVia(); oldxy = site['array_xy']
    # the M5 strap (same net, horizontal, covering x0,y0) and the M4 rail (same net, vertical, covering x0,y0)
    strap = [rect(q) for s in n.getSWires() for q in s.getWires() if not q.isVia() and q.getTechLayer().getName() == 'met5'
             and q.xMin() <= x0 <= q.xMax() and q.yMin() <= y0 <= q.yMax()]
    assert strap, key; st = min(strap, key=lambda r: r[3] - r[1])
    m4ys = [nd[2] for v in viol for nd in (v['node0'], v['node1']) if nd[0] == 'met4']
    down = sum(y < y0 for y in m4ys) >= sum(y > y0 for y in m4ys)
    cols, rows = (2, 4) if cur <= 0.0096 else (2, 6) if cur <= 0.0144 else (2, 8)
    cw, ch = 800 * cols + 800 * (cols - 1), 800 * rows + 800 * (rows - 1)
    bx, by, tx, ty = 190, 190, 310, 310
    bw, bh, tw, th = cw + 2 * bx, ch + 2 * by, cw + 2 * tx, ch + 2 * ty
    ny = st[3] - th // 2 if down else st[1] + th // 2
    bottom = (x0 - bw // 2, ny - bh // 2, x0 + bw // 2, ny + bh // 2); upper = (x0 - tw // 2, ny - th // 2, x0 + tw // 2, ny + th // 2)
    patch = (x0 - 1400, min([bottom[1]] + m4ys) - 1400, x0 + 1400, max([bottom[3]] + m4ys) + 1400)
    assert contains(patch, bottom)
    opp5 = [rect(q) for s in b.findNet(opposite).getSWires() for q in s.getWires() if not q.isVia() and q.getTechLayer().getName() == 'met5']
    opp4 = [rect(q) for s in b.findNet(opposite).getSWires() for q in s.getWires() if not q.isVia() and q.getTechLayer().getName() == 'met4']
    if any(distance(z, upper) < 1600 for z in opp5) or any(distance(z, patch) < 1600 for z in opp4):
        failed.append({'site': list(key), 'reason': 'opposite-net clearance'}); print('PG_C_SITE', idx, key, 'FAILED clearance', flush=True); continue
    sig = (cols, rows, bx, by, tx, ty); vname = 'H1_PG_VIA4_' + '_'.join(map(str, sig)); v = b.findVia(vname)
    if v is None:
        v = odb.dbVia.create(b, vname); p0 = oldvia.getViaParams(); params = odb.dbViaParams()
        for prop in props: getattr(params, 'set' + prop)(getattr(p0, 'get' + prop)())
        params.setNumCutCols(cols); params.setNumCutRows(rows)
        for prop, val in zip(('XBottomEnclosure', 'YBottomEnclosure', 'XTopEnclosure', 'YTopEnclosure'), (bx, by, tx, ty)): getattr(params, 'set' + prop)(val)
        v.setViaGenerateRule(oldvia.getViaGenerateRule()); v.setViaParams(params)
    assert sum(q.getTechLayer().getName() == 'via4' for q in v.getBoxes()) == cols * rows
    win = [x0 - 30000, min(patch[1], upper[1]) - 10000, x0 + 30000, max(patch[3], upper[3]) + 10000]
    baseline = drc(win, f'{idx}_base'); shape = str(box.getWireShapeType())
    odb.dbSBox.destroy(box); new = odb.dbSBox.create(sw, v, x0, ny, shape); assert new
    pbox = odb.dbSBox.create(sw, met4, *patch, 'STRIPE'); assert pbox
    observed = drc(win, f'{idx}_try')
    if not (observed - baseline):
        accepted.append({'site': list(key), 'net': net, 'current_28mW_A': cur, 'prior_array_xy': list(oldxy), 'prior_via': oldvia.getName(),
                         'new_xy': [x0, ny], 'new_via': vname, 'cuts': cols * rows, 'm4_patch': list(patch), 'current_flows_down': down,
                         'screen_violations_at_site': len(viol), 'local_markers_before': sum(baseline.values()), 'local_markers_after': sum(observed.values())})
        print('PG_C_SITE', idx, key, 'accepted', (cols, rows), 'patch', patch, flush=True)
    else:
        odb.dbSBox.destroy(pbox); odb.dbSBox.destroy(new); assert odb.dbSBox.create(sw, oldvia, *oldxy, shape)
        failed.append({'site': list(key), 'reason': 'new local DRC markers', 'new_markers': [list(k) for k in (observed - baseline)]})
        print('PG_C_SITE', idx, key, 'FAILED drc', dict(observed - baseline), flush=True)

after = fixed(b)
assert after[:2] == before[:2] and wires(b) == old_wires and guides(b) == old_guides and obstructions(b) == old_obs
out_odb = OUT / 'fault_v_asic_top.odb'; odb.write_db(db, str(out_odb))
record = {'pass': 'c (H0 PG_C/PG_D: 2-column arrays on 2.8 um M4 patches at remaining EM sites)', 'source_ODB_sha256': sha(SRC),
          'output_ODB_sha256': sha(out_odb), 'screen_used': os.environ['SCREEN_JSON'], 'sites': len(hot), 'accepted': accepted, 'failed': failed,
          'all_cells_graph_signal_wires_guides_obstructions_unchanged': True,
          'scope': 'PG shapes only. Full-chip native DRC, KLayout DRC, LVS, PG contacts, IR/EM and fill are rerun on the final candidate.'}
(OUT / 'pg_h1_fix.json').write_text(json.dumps(record, indent=2) + '\n')
print('PG_H1_FIX_DONE accepted', len(accepted), 'failed', len(failed), record['output_ODB_sha256'], flush=True)
