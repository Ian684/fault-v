"""Read-only remote-via search on exported exact-source routing geometry."""
from pathlib import Path
from collections import defaultdict
import ast,bisect,collections,functools,heapq,json,math,time
C=Path(__file__).resolve().parents[1];raw=json.loads((C/'reports/native_corner_geometry/obstacles.json').read_text());name='net3347'
width={'met1':140,'met2':140,'met3':300,'met4':300,'met5':1600};spacing={'met1':140,'met2':140,'met3':300,'met4':300,'met5':1600,'via':170,'via2':200,'via3':200,'via4':800}
byactual={v['actual']:v for v in raw['vias']};specs=[{**v,'name':v['actual']+'@bare','boxes':v['real'],'pad':None} for v in byactual.values()];existing=defaultdict(list)
for q in raw['target_primitives']:
    if q[0]=='T' and q[1] in byactual:existing[q[2],q[3]].append(tuple(map(tuple,byactual[q[1]]['real'])))
hit=lambda a,b:a[0]<=b[2] and a[2]>=b[0] and a[1]<=b[3] and a[3]>=b[1]
roi=[1570000,624000,1600000,663000];assert raw['bounds'][0]<=roi[0]<roi[2]<=raw['bounds'][2] and raw['bounds'][1]<=roi[1]<roi[3]<=raw['bounds'][3]
env={'collections':collections,'functools':functools,'heapq':heapq,'bisect':bisect,'math':math,'time':time,'spacing':spacing,'width':width,'layername':lambda n:'met'+str(n),'bucket':defaultdict(list),'data':{'vias':specs,'region':roi},'shapes':[q for q in raw['shapes'] if hit(q[1:5],roi)],'existing':existing}
source=(C/'controls/li1_bridge_a_impl.py').read_text();tree=ast.parse(source);names={'rebuild','clear','wireok','viaok','search'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
code='\n'.join(ast.get_source_segment(source,n) for n in nodes)
for f,size in [('clear',350000),('wireok',350000),('viaok',200000)]:code=code.replace('def '+f+'(',f'@functools.lru_cache({size})\ndef '+f+'(')
code=code.replace('if n==net:continue','if n==net and l in width:continue').replace('time.monotonic()-began>180','time.monotonic()-began>40')
needle='    xs=sorted(x for x in xs if loX<=x<=hiX);ys=sorted(y for y in ys if loY<=y<=hiY)';assert code.count(needle)==1
code=code.replace(needle,'    xs.update(x for x,y in existing if loX<=x<=hiX);ys.update(y for x,y in existing if loY<=y<=hiY)\n'+needle)
exec(compile(code,'bounded_offline_remote_search','exec'),env)
@functools.lru_cache(200000)
def viaok(target,vi,x,y):
    s=specs[vi]
    if tuple(map(tuple,s['real'])) in existing.get((x,y),[]):return True
    return all(env['clear'](target,l,x+a,y+b,x+c,y+d) for l,a,b,c,d in s['boxes'])
env['viaok']=viaok;env['rebuild']();attempts=[];found=None
for y,ex,ey in [(631550,1585390,643450),(630870,1585390,643450),(633250,1585390,643450),(630870,1585390,650000),(631550,1585390,655010),(635630,1585390,643450)]:
    start=(1580330,y,2);end=(ex,ey,2);path=env['search'](name,start,end)
    attempts.append({'start':start,'end':end,'path_found':path is not None})
    if path is not None:found={'start':start,'end':end,'path':path};break
out=C/'reports/remote_corner_plan_b.json';assert not out.exists();out.write_text(json.dumps({'read_only':True,'M3_minimum_area':'Via-only M3 islands require a separately checked legal landing patch; natural M3 wire components need no unconditional symmetric pad.','source':'native_group_c','source_sha256':json.loads((C/'reports/native_group_c/result.json').read_text())['output_sha256'],'region':roi,'attempts':attempts,'found':found,'eligible_for_native_trial':found is not None,'accepted_for_final':False,'scope':'Remote bridge search only. It does not create or accept physical geometry; exact-source application, native/context DRC, connectivity and all downstream gates are mandatory.'},indent=2)+'\n')
print('REMOTE_CORNER_PLAN',found is not None,len(attempts),flush=True)
