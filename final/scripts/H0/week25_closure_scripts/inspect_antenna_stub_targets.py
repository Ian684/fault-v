"""Read-only diagnostic of local diode access distances to the preserved signal copper."""
from pathlib import Path
import json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
C=Path('/work/week25_closure')
db,b=load('/runtime_final/antenna_ready.odb');rd,rb=load('/runtime_final/focus_pg.odb')
access=json.loads((C/'reports/antenna_access.json').read_text());rows=[]
for name in sorted(access['borrowed_native_accesses']):
    i=b.findInst(name);p=i.findITerm('DIODE');x,y=i.getLocation()
    ap=list(p.getPrefAccessPoints());assert ap
    points=[(x+a.getPoint()[0],y+a.getPoint()[1],a.getLayer().getName()) for a in ap]
    n=p.getNet().getName();wire=rb.findNet(n).getWire();assert wire
    choices=[]
    for q in primitives(wire)[0]:
        if q[0]!='S' or q[1] not in ('li1','met1','met2'):continue
        _,layer,x1,y1,x2,y2,*_=q
        for ax,ay,al in points:
            tx=min(max(ax,x1),x2);ty=min(max(ay,y1),y2)
            distance=abs(tx-ax)+abs(ty-ay)+(0 if al==layer else 500)
            choices.append((distance,layer,tx,ty,q))
    choices.sort()
    rows.append({'diode':name,'net':n,'access_points':points,'closest_preserved_segments':choices[:12]})
(C/'reports/antenna_stub_targets.json').write_text(json.dumps({'read_only':True,'diodes':rows},indent=2)+'\n')
print('LOCAL_DIODE_COPPER_DISTANCES',[(r['diode'],r['net'],r['closest_preserved_segments'][0][:4]) for r in rows],flush=True)
