"""Convert a GDSII layout to OASIS with KLayout and prove hierarchical equivalence.
Usage: python3 gds_to_oasis.py <src.gds[.gz]> <dst.oas> <report.json> [--negative-control]

Checks (all must pass, exit 0):
 1. per cell and layer, the SET of distinct shapes (box/polygon/path/text, exact coordinates, text string) is identical;
    the only allowed count difference is exact duplicate shapes in the GDS (same cell, layer and geometry), which the
    OASIS writer stores once. Their number is recorded and must equal the shape-count difference exactly.
 2. pya.LayoutDiff with IgnoreDuplicates (cells, instances, layers, dbu, shapes, texts, properties) reports no difference.
 3. cell names, instance counts, dbu and top bbox identical.
--negative-control: deletes one unique (non-duplicated) top-cell met1 shape in memory from the OASIS view and requires
both checks 1 and 2 to fail. The flat geometry XOR is a separate step (xor_layouts.drc)."""
import collections, hashlib, json, sys, time
from pathlib import Path
import pya

src, dst, rep = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
neg = '--negative-control' in sys.argv[4:]
assert src.is_file() and not dst.exists()
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
t0 = time.time()
a = pya.Layout(); a.read(str(src))
assert [c.name for c in a.top_cells()] == ['fault_v_asic_top']
opt = pya.SaveLayoutOptions(); opt.format = 'OASIS'
opt.oasis_compression_level = 10; opt.oasis_strict_mode = True; opt.oasis_write_cblocks = True
opt.oasis_write_cell_bounding_boxes = True; opt.oasis_write_std_properties = 1
part = dst.with_name(dst.name + '.part'); assert not part.exists()
a.write(str(part), opt); part.rename(dst)
b = pya.Layout(); b.read(str(dst))

def shape_key(s):
    # OASIS TEXT records carry only string, layer/texttype and position: GDS text orientation, size and alignment are
    # presentation attributes OASIS cannot represent, so texts are compared by string + displacement (counted below).
    if s.is_text(): t = s.text; return ('T', t.string, t.trans.disp.x, t.trans.disp.y)
    if s.is_box() or s.is_polygon() or s.is_path() or s.is_simple_polygon(): return ('P', str(s.polygon))
    return ('O', str(s))
def shape_sets(l):
    out = {}
    for ci in range(l.cells()):
        cell = l.cell(ci)
        for li in l.layer_indexes():
            info = l.get_info(li)
            c = collections.Counter(shape_key(s) for s in cell.shapes(li).each())
            if c: out[(cell.name, info.layer, info.datatype)] = c
    return out
def compare_sets(sa, sb):
    keys = set(sa) | set(sb); mismatched = []; dup_a = dup_b = 0
    for k in keys:
        ca, cb = sa.get(k, collections.Counter()), sb.get(k, collections.Counter())
        if set(ca) != set(cb): mismatched.append(k)
        dup_a += sum(ca.values()) - len(ca); dup_b += sum(cb.values()) - len(cb)
    return mismatched, dup_a, dup_b

def text_presentation(l):
    n = collections.Counter()
    for ci in range(l.cells()):
        for li in l.layer_indexes():
            for s in l.cell(ci).shapes(li).each():
                if s.is_text():
                    t = s.text; n['texts'] += 1
                    if t.trans.rot != 0 or t.trans.is_mirror(): n['rotated_or_mirrored'] += 1
                    if t.size != 0: n['nonzero_size'] += 1
                    if int(t.halign) >= 0 or int(t.valign) >= 0: n['aligned'] += 1
    return dict(n)
FLAGS = (pya.LayoutDiff.BoxesAsPolygons | pya.LayoutDiff.PathsAsPolygons | pya.LayoutDiff.IgnoreDuplicates | pya.LayoutDiff.Silent
         | pya.LayoutDiff.NoTextOrientation | getattr(pya.LayoutDiff, 'NoTextDetails', 0))
def layout_diff(x, y): return bool(pya.LayoutDiff().compare(x, y, FLAGS))
def struct(l):
    return {'cells': sorted(l.cell(ci).name for ci in range(l.cells())),
            'instances': sum(l.cell(ci).child_instances() for ci in range(l.cells())), 'dbu': l.dbu,
            'top_bbox': str(l.top_cell().bbox()),
            'layers': sorted((l.get_info(i).layer, l.get_info(i).datatype) for i in l.layer_indexes())}

sa, sb = shape_sets(a), shape_sets(b)
mismatched, dup_a, dup_b = compare_sets(sa, sb)
na = sum(sum(c.values()) for c in sa.values()); nb = sum(sum(c.values()) for c in sb.values())
dup_cells = collections.Counter()
for k, c in sa.items():
    d = sum(c.values()) - len(c)
    if d: dup_cells[k[0]] += d
st_a, st_b = struct(a), struct(b)
ld = layout_diff(a, b)
record = {'source': str(src), 'source_sha256': sha(src), 'source_bytes': src.stat().st_size,
          'oasis': str(dst), 'oasis_sha256': sha(dst), 'oasis_bytes': dst.stat().st_size,
          'klayout_python_version': getattr(pya, '__version__', 'unknown'),
          'oasis_options': {'compression_level': 10, 'strict_mode': True, 'cblocks': True, 'cell_bboxes': True, 'std_properties': 1},
          'cells': len(st_a['cells']), 'instances': st_a['instances'], 'layers': len(st_a['layers']),
          'shapes_gds': na, 'shapes_oasis': nb, 'exact_duplicate_shapes_in_gds': dup_a, 'exact_duplicate_shapes_in_oasis': dup_b,
          'duplicates_by_cell_top10': dup_cells.most_common(10),
          'distinct_shape_sets_identical_per_cell_layer': not mismatched, 'mismatched_cell_layers': [list(k) for k in mismatched[:20]],
          'count_difference_equals_duplicates': na - nb == dup_a - dup_b,
          'structure_identical': st_a == st_b,
          'text_presentation_gds': text_presentation(a), 'text_presentation_oasis': text_presentation(b),
          'text_note': 'OASIS stores text string + position only; GDS text orientation/size/alignment (display attributes) are not representable. GDSII remains the primary deliverable.',
          'layoutdiff_flags': 'BoxesAsPolygons|PathsAsPolygons|IgnoreDuplicates|NoTextOrientation' + ('|NoTextDetails' if getattr(pya.LayoutDiff, 'NoTextDetails', 0) else ''),
          'layoutdiff_ignore_duplicates_identical': ld}
record['equivalent'] = (not mismatched) and record['count_difference_equals_duplicates'] and record['structure_identical'] and ld
if neg:
    c = b.top_cell(); li = b.find_layer(68, 20)
    cnt = sb[('fault_v_asic_top', 68, 20)]
    victim = next(s for s in c.shapes(li).each() if not s.is_text() and cnt[shape_key(s)] == 1)
    desc = str(victim); c.shapes(li).erase(victim)
    mm, _, _ = compare_sets(sa, shape_sets(b))
    record['negative_control'] = {'deleted_unique_top_cell_met1_shape': desc, 'set_check_detected': bool(mm),
                                  'layoutdiff_detected': not layout_diff(a, b)}
    record['negative_control']['detected'] = record['negative_control']['set_check_detected'] and record['negative_control']['layoutdiff_detected']
record['elapsed_s'] = round(time.time() - t0, 1)
rep.write_text(json.dumps(record, indent=2) + '\n')
print('OASIS_CONVERT', dst.name, 'equivalent', record['equivalent'], 'dups', dup_a, dup_b, 'neg', record.get('negative_control', {}).get('detected'), flush=True)
ok = record['equivalent'] and (not neg or record['negative_control']['detected'])
sys.exit(0 if ok else 3)
