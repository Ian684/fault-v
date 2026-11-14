"""H1 PG repair pass e (openroad -python): two remaining 28 mW EM sites after pass d.
 A  VGND array at site (122230, 2372600): current enters only the cuts under the 3 um M5 strap -> same-net M5 patch over
    the whole array top enclosure (+0.3 um), widening the strap locally so all 12 cuts share the current (real metal).
 B  VGND M4 rail x=2346870 between 840.27 and 869.82 um (12.07 mA on 1.74 um) -> extend the 2.8 um M4 patch down to 838.87 um
    (same as the mirrored site at x=122230).
Each patch is accepted only if the local native DRC window shows no new marker.
Env: SRC_ODB (pass-d output), PASS_D_JSON, OUT_DIR."""
import hashlib, json, os, re, sys
from collections import Counter
from pathlib import Path
import odb
from openroad import Tech, Design
sys.path.insert(0, '/work/routing/scripts')
from temporary_fixed_routes import fixed, wires, guides, obstructions

SRC = Path(os.environ['SRC_ODB']); OUT = Path(os.environ['OUT_DIR']); OUT.mkdir(parents=True, exist_ok=False)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
pd = json.loads(Path(os.environ['PASS_D_JSON']).read_text()); assert pd['output_ODB_sha256'] == sha(SRC)
t = Tech(); design = Design(t); design.readDb(str(SRC)); db = design.getDb(); b = db.getChip().getBlock(); tech = db.getTech()
design.evalTclString('set_thread_count 4')
before = fixed(b); old_wires = wires(b); old_guides = guides(b); old_obs = obstructions(b)


def drc(box, tag):
    design.getTritonRoute().clearDesign(); p = OUT / f'{tag}.rpt'
    design.evalTclString(f'drt::check_drc -box {{{" ".join(map(str, box))}}} -output_file {p} -marker_name PGH1E')
    text = p.read_text(); rows = re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)', text)
    assert len(rows) == text.count('violation type:'); p.unlink(); return Counter(rows)


site = next(r for r in pd['accepted'] if r['site'] == ['VGND', 122230, 2372600])
via = b.findVia(site['new_via']); x, y = site['new_xy']
top = next(q for q in via.getBoxes() if q.getTechLayer().getName() == 'met5')
m5patch = (x + top.xMin() - 300, y + top.yMin() - 300, x + top.xMax() + 300, y + top.yMax() + 300)
m4patch = (2345470, 838870, 2348270, 869820 + 1400)
results = []
sw = next(iter(b.findNet('VGND').getSWires()))
for tag, layer, box in (('A_m5', 'met5', m5patch), ('B_m4', 'met4', m4patch)):
    win = [box[0] - 30000, box[1] - 10000, box[2] + 30000, box[3] + 10000]
    base = drc(win, tag + '_base')
    s = odb.dbSBox.create(sw, tech.findLayer(layer), *box, 'STRIPE'); assert s
    obs = drc(win, tag + '_try'); ok = not (obs - base)
    if not ok: odb.dbSBox.destroy(s)
    results.append({'patch': tag, 'net': 'VGND', 'layer': layer, 'box': list(box), 'accepted': ok,
                    'local_markers_before': sum(base.values()), 'local_markers_after': sum(obs.values()),
                    'new_markers': [list(k) for k in (obs - base)]})
    print('PG_E_PATCH', tag, layer, box, 'accepted' if ok else 'FAILED', dict(obs - base), flush=True)
after = fixed(b)
assert after[:2] == before[:2] and wires(b) == old_wires and guides(b) == old_guides and obstructions(b) == old_obs
out_odb = OUT / 'fault_v_asic_top.odb'; odb.write_db(db, str(out_odb))
record = {'pass': 'e (M5 strap widening over one array, M4 patch extension)', 'source_ODB_sha256': sha(SRC), 'output_ODB_sha256': sha(out_odb),
          'patches': results, 'all_cells_graph_signal_wires_guides_obstructions_unchanged': True}
(OUT / 'pg_h1_fix.json').write_text(json.dumps(record, indent=2) + '\n')
print('PG_H1_FIX_DONE patches', sum(r['accepted'] for r in results), 'of', len(results), record['output_ODB_sha256'], flush=True)
