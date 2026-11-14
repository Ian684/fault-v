from pathlib import Path
C=Path('/work/week25_closure')
code=(C/'scripts/inspect_remaining_shorts.py').read_text()
for old,new in [('/runtime/focus_final.odb','/route_b/1-openroad-detailedrouting/native_final.odb'),('reports/focus_finish_independent.json','reports/short_b_final_independent.json'),('reports/remaining_short_geometry.json','reports/final_short_geometry.json')]:
    assert code.count(old)==1;code=code.replace(old,new)
exec(compile(code,'read_only_final_short_geometry','exec'))
