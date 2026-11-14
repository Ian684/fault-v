"""Search between free interior copper points instead of pin-obstructed route endpoints."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'controls/final_paths_b_impl.py').read_text()
code=code.replace('/route_b/1-openroad-detailedrouting/native_final.odb','/runtime/signal_polished.odb').replace('reports/final_paths_b','reports/interior_bridge_a').replace('final_paths_b.odb','interior_bridge_a.odb')
code=code.replace('assert sum(current.values())==4','assert sum(current.values())==3')
start=code.index('plans=[\n');end=code.index('\naccepted=[];',start)
code=code[:start]+'''plans=[
 ('_09360_',[segment('met1',(1588105,636650),(1595970,636650))],(1590000,636650,1),(1594000,636650,1)),
]'''+code[end:]
needle='    path=search(name,start,end)\n';assert code.count(needle)==1
code=code.replace(needle,needle+'''    if path is not None:
        path=[{'from':(1588105,636650,1),'to':start,'via':None}]+path+[{'from':end,'to':(1595970,636650,1),'via':None}]
''')
p=C/'controls/interior_bridge_a_impl.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,encoding='utf-8')
