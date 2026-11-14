"""Export signal/clock and SRAM input targets from the exact filled H1 database.

H0 method (week25_closure/scripts/export_closure_activity_targets.py) with H1 paths. Runs inside the pinned image:
openroad -exit -python signoff/export_activity_targets_c.py <filled odb> <tag>
"""
from pathlib import Path
import hashlib, json, re, sys, odb

H = Path('/work/ppa/h1/cand_gap90x95')
source = Path(sys.argv[1])
tag = sys.argv[2]
assert re.fullmatch('[a-z0-9_]+', tag)
out = H / 'functional' / tag
receipt = json.loads((out / 'result.json').read_text())
assert receipt['all_reset_CDC_and_four_workloads_pass']
db = odb.dbDatabase.create()
odb.read_db(db, str(source))
b = db.getChip().getBlock()
normalize = lambda s: s.replace('\\', '')
signals = sorted(normalize(n.getName()) for n in b.getNets()
                 if n.getWire() and str(n.getSigType()) not in ('POWER', 'GROUND'))
assert len(signals) == len(set(signals)) and len(signals) > 30000, len(signals)
macros = {i.getName(): {t.getMTerm().getName(): normalize(t.getNet().getName()) for t in i.getITerms()
                        if t.getNet() and str(t.getSigType()) not in ('POWER', 'GROUND') and str(t.getIoType()) == 'INPUT'}
          for i in b.getInsts() if i.getMaster().isBlock()}
assert len(macros) == 18
with source.open('rb') as f:
    digest = hashlib.file_digest(f, 'sha256').hexdigest()
p = out / 'activity_targets.json'
assert not p.exists()
p.write_text(json.dumps({'candidate_ODB_sha256': digest, 'candidate_netlist_sha256': receipt['netlist_sha256'],
                         'routed_signal_clock_nets': signals, 'SRAM_input_nets': macros, 'clock_net': 'clk'}, indent=2) + '\n')
print('H1_ACTIVITY_TARGETS', tag, len(signals), digest, flush=True)
