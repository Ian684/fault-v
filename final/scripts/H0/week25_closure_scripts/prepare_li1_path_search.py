"""Include actual LI1/mcon geometry when searching short local copper underpasses."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'controls/interior_bridge_a_impl.py').read_text()
code=code.replace("source=Path('/runtime/signal_polished.odb')","source=Path('/runtime_final/wide_notch_b.odb')")
code=code.replace('reports/interior_bridge_a','reports/li1_bridge_a').replace('interior_bridge_a.odb','li1_bridge_a.odb').replace('assert sum(current.values())==3','assert sum(current.values())==2')
code=code.replace("('met1','met2','met3','met4'):","('li1','met1','met2','met3','met4'):")
code=code.replace("'via4':800}","'via4':800,'li1':170,'mcon':190}")
code=code.replace("width={l:tech.findLayer(l).getWidth() for l in ('met1','met2','met3','met4','met5')}","width={l:tech.findLayer(l).getWidth() for l in ('li1','met1','met2','met3','met4','met5')}\nlayername=lambda n:'li1' if n==0 else 'met'+str(n)\nassert width['li1']==170 and tech.findLayer('mcon').getSpacing()==190")
code=code.replace("lo=int(v['lo'][-1]);hi=int(v['hi'][-1])","lo=0 if v['lo']=='li1' else int(v['lo'][-1]);hi=0 if v['hi']=='li1' else int(v['hi'][-1])")
code=code.replace("l='met'+str(L)","l=layername(L)")
code=code.replace("'met'+str(start[2])","layername(start[2])").replace("'met'+str(end[2])","layername(end[2])").replace("'met'+str(a[2])","layername(a[2])").replace("'met'+str(z[2])","layername(z[2])")
start=code.index('plans=[\n');end=code.index('\naccepted=[];',start)
code=code[:start]+'''pgpoints=[(1607930,632910),(1608850,632910),(1608850,633250),(1610230,633250),(1610230,634270),(1610690,634270),(1610690,634780),(1612070,634780)]
plans=[
 ('_09360_',[segment('met1',(1588105,636650),(1595970,636650))],(1590000,636650,1),(1594000,636650,1)),
 ('net6342',[segment('met2',a,z) for a,z in zip(pgpoints,pgpoints[1:])],(1607930,632910,2),(1612070,634780,2)),
]'''+code[end:]
code=code.replace("if path is not None:\n        path=", "if path is not None and name=='_09360_':\n        path=")
p=C/'controls/li1_bridge_a_impl.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,encoding='utf-8')
