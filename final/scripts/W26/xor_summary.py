"""Summarise a flat XOR run: xor_summary.py <report.rdb> <klayout log> <rc> <out.json> [removed-shape info.json]"""
import hashlib, json, re, sys
from pathlib import Path
rdb, log, rc, out = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
t = rdb.read_text(errors='replace'); lt = log.read_text(errors='replace')
m = re.search(r'XOR layers: (\d+)', lt)
cats = re.findall(r"<category>'?([^<']+)'?</category>", t)
rec = {'rc': rc, 'layers': int(m.group(1)) if m else None, 'items': t.count('<item>'),
       'categories_with_items': sorted(set(cats)), 'report_sha256': hashlib.sha256(rdb.read_bytes()).hexdigest(),
       'method': 'KLayout DRC flat XOR, 500 um tiles, every polygon layer present in either layout (w26/scripts/xor_layouts.drc)'}
if len(sys.argv) > 5: rec['removed_shape'] = json.loads(Path(sys.argv[5]).read_text()); rec['detected'] = rec['items'] > 0 and rc == 0
out.write_text(json.dumps(rec, indent=2) + '\n')
print('XOR_SUMMARY', out.name, rec['rc'], rec['layers'], rec['items'])
