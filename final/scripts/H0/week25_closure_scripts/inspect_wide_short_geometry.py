from pathlib import Path
C=Path('/work/week25_closure')
code=(C/'scripts/inspect_remaining_shorts.py').read_text()
for a,z in [('/runtime/focus_final.odb','/runtime/signal_polished.odb'),('reports/focus_finish_independent.json','reports/wide_b_independent.json'),('reports/remaining_short_geometry.json','reports/wide_short_geometry.json'),('for q in primitives(net.getWire())[0]:','for q in (primitives(net.getWire())[0] if net.getWire() else []):')]:
    assert code.count(a)==1;code=code.replace(a,z)
needle="check=json.loads((C/'reports/wide_b_independent.json').read_text());result=[]"
assert code.count(needle)==1
code=code.replace(needle,"check=json.loads((C/'reports/wide_b_independent.json').read_text());check['unresolved'].append({'srcs':'net:net8601','bbox_dbu':[1591600,636400,1592100,637000],'layer':'met2'});result=[]")
exec(compile(code,'read_only_wide_geometry_and_neighbor','exec'))
