"""Reuse the verified streaming parser without writing to frozen PPA preparation evidence."""
from pathlib import Path
import re,sys
C=Path(__file__).resolve().parents[1];tag=sys.argv[1];assert re.fullmatch('[a-z0-9_]+',tag)
source=C.parent/'ppa/scripts/analyze_activity.py';code=source.read_text()
for a,z in [("p=Path(__file__).resolve().parents[1]",f"p=Path({str(C/'functional'/tag)!r})"),("p/'reports/activity_generation.json'","p/'result.json'"),("p/'reports/activity_targets.json'","p/'activity_targets.json'"),("p/'reports/activity_coverage.json'","p/'activity_coverage.json'"),("receipt['limitations']","[receipt['scope']]"),("file=p/run['vcd'];",f"file=Path({str(C)!r})/Path(run['vcd']).relative_to('/work/week25_closure');")]:
    assert code.count(a)==1,a;code=code.replace(a,z)
start=code.index("    (p/'WORK_STATE.json').write_text(");end=code.index('\n\nif __name__',start)
code=code[:start]+code[end:]
assert '/reports/' not in code and 'WORK_STATE' not in code
exec(compile(code,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
