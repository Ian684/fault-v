"""Derive a bounded same-layer detour around the actual power landing pad."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/repair_final_crossings.py').read_text()
code=code.replace("source=Path('/route_b/1-openroad-detailedrouting/native_final.odb')","source=Path('/runtime_final/wide_notch_b.odb')")
start=code.index("proof=json.loads(");end=code.index('\nt=Tech();',start)
code=code[:start]+'''proof=json.loads((C/'reports/wide_notch_b/result.json').read_text());assert proof['remaining_local_markers']==2 and sha(source)==proof['output_sha256']
conn=json.loads((C/'reports/wide_b_all_connectivity.json').read_text());assert conn['source_sha256']==proof['source_sha256'] and conn['all_signal_geometry_connected']
'''+code[end:]
code=code.replace('reports/final_crossings_a','reports/manual_pg_signal_a').replace('final_crossings.odb','manual_pg_signal_a.odb')
code=code.replace('1578000 628000 1622000 642000','1575000 620000 1630000 662000').replace('assert sum(current.values())==4','assert sum(current.values())==2')
start=code.index('plans=[]\n');end=code.index('\ndone=set()',start)
code=code[:start]+'''plans=[]
points=[(1607930,632910),(1608850,632910),(1608850,633250),(1610230,633250),(1610230,634270),(1610690,634270),(1610690,634780),(1612070,634780)]
cuts=[segment('met2',a,z) for a,z in zip(points,points[1:])]
for x in (1608390,1608150,1607930,1608290,1608490,1607830,1607470):
    for y in (634780,634950,635120):
        path=[(1607930,632910,'met2'),(x,632910,'met2'),(x,y,'met2'),(1612070,y,'met2'),(1612070,634780,'met2')]
        plans.append(('net6342',cuts,path,[x,y]))
'''+code[end:]
p=C/'controls/manual_pg_signal_a_impl.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,encoding='utf-8')
