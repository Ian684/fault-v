"""Inspect the conservative planner's actual blocking shapes, without editing layout."""
from pathlib import Path
import collections,functools,heapq,json
C=Path(__file__).resolve().parents[1]
data=json.loads((C/'reports/final_paths_b/obstacles.json').read_text());shapes=data['shapes']
code=(C/'scripts/compressed_path_planner.py').read_text().replace("width={l:tech.findLayer(l).getWidth() for l in ('met1','met2','met3','met4','met5')}","width={'met1':140,'met2':140,'met3':300,'met4':300,'met5':1600}")
exec(compile(code,'planner_geometry_only','exec'));rebuild()
def blockers(net,vi,x,y):
    rows=[]
    for l,a,b,c,d in data['vias'][vi]['boxes']:
        x1,y1,x2,y2=x+a,y+b,x+c,y+d;sp=spacing[l]
        for ll,A,B,Z,F,n in shapes:
            if ll!=l or n==net:continue
            dx=max(A-x2,x1-Z,0);dy=max(B-y2,y1-F,0)
            if dx*dx+dy*dy<sp*sp:rows.append([l,A,B,Z,F,n])
    return rows
for net,x,y in [('_03544_',1613910,629340),('net6342',1608850,633250),('_09360_',1588105,636650)]:
    print('POINT',net,x,y)
    for vi,v in enumerate(data['vias']):
        if v['name'].endswith('_PR'):print(v['name'],blockers(net,vi,x,y)[:8])
code=(C/'scripts/compressed_path_planner.py').read_text();a=code.index('def search(');code=code[a:]
code=code.replace("print('NO_PATH',net,count,dict(collections.Counter(z[2] for z in cost)),flush=True)","print('NO_PATH',net,count,{L:([min(s[0] for s in cost if s[2]==L),min(s[1] for s in cost if s[2]==L),max(s[0] for s in cost if s[2]==L),max(s[1] for s in cost if s[2]==L)]) for L in {s[2] for s in cost}},flush=True)")
exec(compile(code,'planner_reachability','exec'))
data['region']=[1607910,623340,1622210,637550]
search('_03544_',(1613910,629340,2),(1616210,631550,2))
