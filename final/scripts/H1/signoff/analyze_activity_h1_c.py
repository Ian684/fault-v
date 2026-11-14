"""Reuse the verified streaming VCD parser (ppa/scripts/analyze_activity.py) on the H1 activity, as H0 did in
week25_closure/scripts/analyze_closure_activity.py. Writes only cand_gap90x95/functional/<tag>/activity_coverage.json.
Runs inside the pinned image: python3 signoff/analyze_activity_h1_c.py <tag>
"""
from pathlib import Path
import re, sys

H = Path('/work/ppa/h1/cand_gap90x95')
tag = sys.argv[1]
assert re.fullmatch('[a-z0-9_]+', tag)
source = Path('/work/ppa/scripts/analyze_activity.py')
code = source.read_text()
# run['vcd'] is an absolute /work path in the H1 receipt, so p/run['vcd'] already resolves to the VCD itself
for a, z in [("p=Path(__file__).resolve().parents[1]", f"p=Path({str(H / 'functional' / tag)!r})"),
             ("p/'reports/activity_generation.json'", "p/'result.json'"),
             ("p/'reports/activity_targets.json'", "p/'activity_targets.json'"),
             ("p/'reports/activity_coverage.json'", "p/'activity_coverage.json'"),
             ("receipt['limitations']", "[receipt['scope']]")]:
    assert code.count(a) == 1, a
    code = code.replace(a, z)
start = code.index("    (p/'WORK_STATE.json').write_text(")
end = code.index('\n\nif __name__', start)
code = code[:start] + code[end:]
assert '/reports/' not in code and 'WORK_STATE' not in code
assert not (H / 'functional' / tag / 'activity_coverage.json').exists()
exec(compile(code, str(source), 'exec'), {'__file__': str(source), '__name__': '__main__'})
