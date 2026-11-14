"""Respect same-net cut spacing while reusing exact vias and bounded local goals."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs_d.py').read_text().replace('antenna_stubs_d','antenna_stubs_e').replace('reports/antenna_stubs_c/incomplete.json','reports/antenna_stubs_d/incomplete.json')
marker="xy=[p[:2] for p in row['access_points']]+[p[2:4] for p in row['closest_preserved_segments'][:8]]"
assert code.count(marker)==1
code=code.replace(marker,"xy=[p[:2] for p in row['access_points']]+[p[2:4] for p in row['closest_preserved_segments'] if p[0]<=max(20000,row['closest_preserved_segments'][0][0]+10000)]")
marker="exec(compile(source.replace('time.monotonic()-began>180','time.monotonic()-began>35'),'bounded_existing_local_planner','exec'))"
assert code.count(marker)==1
prefix="""assert source.count('if n==net:continue')==1
source=source.replace('if n==net:continue','if n==net and l in width:continue')
needle='    xs=sorted(x for x in xs if loX<=x<=hiX);ys=sorted(y for y in ys if loY<=y<=hiY)'
assert source.count(needle)==1
source=source.replace(needle,'    xs.update(x for n,x,y in native_vias if n==net and loX<=x<=hiX and loY<=y<=hiY)\\n    ys.update(y for n,x,y in native_vias if n==net and loX<=x<=hiX and loY<=y<=hiY)\\n'+needle)
"""
suffix='''
native_vias=defaultdict(list)
via_boxes=lambda v:tuple(sorted((q.getTechLayer().getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax()) for q in v.getBoxes()))
for name in access['cleared_signal_nets']:
    for q in primitives(b.findNet(name).getWire())[0]:
        if q[0] in ('T','V'):
            v=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);native_vias[name,q[2],q[3]].append(via_boxes(v))
candidate_via_boxes=[tuple(sorted(tuple(q) for q in v['boxes'])) for v in vs]
@functools.lru_cache(200000)
def viaok(net,vi,x,y):
    if candidate_via_boxes[vi] in native_vias.get((net,x,y),[]):return True
    return all(clear(net,l,x+a,y+bb,x+c,y+d) for l,a,bb,c,d in data['vias'][vi]['boxes'])
'''
code=code.replace(marker,prefix+marker+suffix)
marker="    added=append(b.findNet(row['net']),row['path'])"
assert code.count(marker)==1
code=code.replace(marker,marker+"\n    replayed=[tuple(q) for q in row['added_primitives'] if q[0]=='R']\n    if replayed:added+=append_patches(b.findNet(row['net']),replayed)")
marker='    for trial,end in enumerate(goals[:6]):'
assert code.count(marker)==1
code=code.replace(marker,marker+'\n        if not (roi[0]<=end[0]<=roi[2] and roi[1]<=end[1]<=roi[3]):continue')
p=C/'scripts/append_antenna_stubs_e.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('CUT_SPACING_EXACT_REUSE_STUB_E_PREPARED')
