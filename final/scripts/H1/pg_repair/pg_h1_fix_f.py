"""H1 PG repair pass f (openroad -python): last 28 mW EM site after pass e, VGND rail x=122230 at the M5 strap y=2372600.
PDNSim credits only the array columns under the 3 um strap (2 cols -> 4 cuts, 10.5 mA -> 1.06x). Replace the 2x6 array by a
3-column array (3x6, 6 cuts under the strap), shifted 1 um toward the die edge to keep >= 0.4 um from the neighbouring VPWR
M4 patch, with the M4 and M5 patches widened to cover it. Accepted only if the local native DRC window shows no new marker;
alternatives 3x4 / shifts are tried in order. Env: SRC_ODB (pass-e output), PASS_D_JSON, PASS_E_JSON, OUT_DIR."""
import hashlib, json, math, os, re, sys
from collections import Counter
from pathlib import Path
import odb
from openroad import Tech, Design
sys.path.insert(0, '/work/routing/scripts')
from temporary_fixed_routes import fixed, wires, guides, obstructions

SRC = Path(os.environ['SRC_ODB']); OUT = Path(os.environ['OUT_DIR']); OUT.mkdir(parents=True, exist_ok=False)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pe = json.loads(Path(os.environ['PASS_E_JSON']).read_text()); assert pe['output_ODB_sha256'] == sha(SRC)
pd = json.loads(Path(os.environ['PASS_D_JSON']).read_text())
t = Tech(); design = Design(t); design.readDb(str(SRC)); db = design.getDb(); b = db.getChip().getBlock(); tech = db.getTech()
design.evalTclString('set_thread_count 4')
before = fixed(b); old_wires = wires(b); old_guides = guides(b); old_obs = obstructions(b)
rect = lambda q: (q.xMin(), q.yMin(), q.xMax(), q.yMax())
distance = lambda a, z: math.hypot(max(a[0] - z[2], z[0] - a[2], 0), max(a[1] - z[3], z[1] - a[3], 0))


def drc(box, tag):
    design.getTritonRoute().clearDesign(); p = OUT / f'{tag}.rpt'
    design.evalTclString(f'drt::check_drc -box {{{" ".join(map(str, box))}}} -output_file {p} -marker_name PGH1F')
    text = p.read_text(); rows = re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)', text)
    assert len(rows) == text.count('violation type:'); p.unlink(); return Counter(rows)


site = next(r for r in pd['accepted'] if r['site'] == ['VGND', 122230, 2372600])
net = b.findNet('VGND'); x0, ny = site['new_xy']
found = [(sw, q) for sw in net.getSWires() for q in sw.getWires() if q.isVia() and tuple(q.getViaXY()) == (x0, ny)]
assert len(found) == 1; sw, box = found[0]; oldvia = box.getBlockVia(); assert oldvia.getName() == site['new_via']
strap_bottom = 2371100
opp4 = [rect(q) for s in b.findNet('VPWR').getSWires() for q in s.getWires() if not q.isVia() and q.getTechLayer().getName() == 'met4']
opp5 = [rect(q) for s in b.findNet('VPWR').getSWires() for q in s.getWires() if not q.isVia() and q.getTechLayer().getName() == 'met5']
props = ('BottomLayer', 'CutLayer', 'TopLayer', 'NumCutCols', 'NumCutRows', 'XCutSize', 'YCutSize', 'XCutSpacing', 'YCutSpacing',
         'XOrigin', 'YOrigin', 'XBottomEnclosure', 'YBottomEnclosure', 'XTopEnclosure', 'YTopEnclosure', 'XBottomOffset',
         'YBottomOffset', 'XTopOffset', 'YTopOffset')
result = None; tried = []
for cols, rows, dx in ((3, 6, -1000), (3, 6, -1200), (3, 4, -1000), (3, 4, -1200)):
    cw, ch = 800 * cols + 800 * (cols - 1), 800 * rows + 800 * (rows - 1)
    bw, bh, tw, th = cw + 380, ch + 380, cw + 620, ch + 620
    cx = x0 + dx; cy = strap_bottom + th // 2
    bottom = (cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2); upper = (cx - tw // 2, cy - th // 2, cx + tw // 2, cy + th // 2)
    m4 = (bottom[0] - 200, 2369820, max(bottom[2] + 200, x0 + 1400), max(2381800, bottom[3] + 200))
    m5 = (upper[0] - 300, upper[1] - 300, max(upper[2] + 300, 124040), max(upper[3] + 300, 2380820))
    if any(distance(z, m4) < 400 for z in opp4) or any(distance(z, m5) < 1600 for z in opp5):
        tried.append({'cols': cols, 'rows': rows, 'dx': dx, 'result': 'clearance'}); continue
    sig = (cols, rows, 190, 190, 310, 310); vname = 'H1_PG_VIA4_' + '_'.join(map(str, sig)); v = b.findVia(vname)
    if v is None:
        v = odb.dbVia.create(b, vname); p0 = oldvia.getViaParams(); params = odb.dbViaParams()
        for prop in props: getattr(params, 'set' + prop)(getattr(p0, 'get' + prop)())
        params.setNumCutCols(cols); params.setNumCutRows(rows)
        for prop in ('XBottomEnclosure', 'YBottomEnclosure'): getattr(params, 'set' + prop)(190)
        for prop in ('XTopEnclosure', 'YTopEnclosure'): getattr(params, 'set' + prop)(310)
        v.setViaGenerateRule(oldvia.getViaGenerateRule()); v.setViaParams(params)
    assert sum(q.getTechLayer().getName() == 'via4' for q in v.getBoxes()) == cols * rows
    win = [min(m4[0], m5[0]) - 30000, min(m4[1], m5[1]) - 10000, max(m4[2], m5[2]) + 30000, max(m4[3], m5[3]) + 10000]
    base = drc(win, 'base'); shape = str(box.getWireShapeType())
    odb.dbSBox.destroy(box); new = odb.dbSBox.create(sw, v, cx, cy, shape); assert new
    p4 = odb.dbSBox.create(sw, tech.findLayer('met4'), *m4, 'STRIPE'); p5 = odb.dbSBox.create(sw, tech.findLayer('met5'), *m5, 'STRIPE')
    obs = drc(win, 'try'); ok = not (obs - base)
    tried.append({'cols': cols, 'rows': rows, 'dx': dx, 'result': 'accepted' if ok else 'drc', 'new_markers': [list(k) for k in (obs - base)]})
    print('PG_F_TRY', cols, rows, dx, 'accepted' if ok else 'FAILED', dict(obs - base), flush=True)
    if ok:
        result = {'site': ['VGND', 122230, 2372600], 'prior_xy': [x0, ny], 'prior_via': oldvia.getName(), 'new_xy': [cx, cy], 'new_via': vname,
                  'cuts': cols * rows, 'm4_patch': list(m4), 'm5_patch': list(m5)}
        break
    odb.dbSBox.destroy(p4); odb.dbSBox.destroy(p5); odb.dbSBox.destroy(new); box = odb.dbSBox.create(sw, oldvia, x0, ny, shape); assert box
after = fixed(b)
assert after[:2] == before[:2] and wires(b) == old_wires and guides(b) == old_guides and obstructions(b) == old_obs
out_odb = OUT / 'fault_v_asic_top.odb'; odb.write_db(db, str(out_odb))
record = {'pass': 'f (3-column array at the last EM site)', 'source_ODB_sha256': sha(SRC), 'output_ODB_sha256': sha(out_odb),
          'accepted': result, 'tried': tried, 'all_cells_graph_signal_wires_guides_obstructions_unchanged': True}
(OUT / 'pg_h1_fix.json').write_text(json.dumps(record, indent=2) + '\n')
print('PG_H1_FIX_DONE', 'accepted' if result else 'none', record['output_ODB_sha256'], flush=True)
