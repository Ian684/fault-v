"""Use real preferred pin accesses and route vias as well as segment projections."""
from pathlib import Path
import json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
C=Path('/work/week25_closure');db,b=load('/runtime_final/antenna_ready.odb');rd,rb=load('/runtime_final/focus_pg.odb');tech=rd.getTech()
access=json.loads((C/'reports/antenna_access.json').read_text());rows=[]
level=lambda n:0 if n=='li1' else int(n[-1])
for name in sorted(access['borrowed_native_accesses']):
    i=b.findInst(name);p=i.findITerm('DIODE');x,y=i.getLocation();ap=list(p.getPrefAccessPoints());assert ap
    points=[(x+a.getPoint()[0],y+a.getPoint()[1],a.getLayer().getName()) for a in ap]
    n=p.getNet().getName();net=rb.findNet(n);wire=net.getWire();assert wire
    choices=[]
    def target(layer,tx,ty,evidence):
        if layer not in ('li1','met1','met2','met3'):return
        distance=min(abs(tx-ax)+abs(ty-ay)+500*abs(level(al)-level(layer)) for ax,ay,al in points)
        choices.append((distance,layer,tx,ty,evidence))
    for q in primitives(wire)[0]:
        if q[0]=='S':
            _,layer,x1,y1,x2,y2,*_=q
            for ax,ay,al in points:target(layer,min(max(ax,x1),x2),min(max(ay,y1),y2),q)
        elif q[0] in ('T','V'):
            v=tech.findVia(q[1]) if q[0]=='T' else rb.findVia(q[1]);vx,vy=q[2:4]
            for layer in (v.getBottomLayer(),v.getTopLayer()):
                if any(z.getTechLayer()==layer and z.xMin()<=0<=z.xMax() and z.yMin()<=0<=z.yMax() for z in v.getBoxes()):target(layer.getName(),vx,vy,q)
    for pin in net.getITerms():
        ox,oy=pin.getInst().getLocation()
        for a in pin.getPrefAccessPoints():
            px,py=a.getPoint();gx,gy=ox+px,oy+py;layer=a.getLayer().getName()
            assert any(l.getName()==layer and q.xMin()<=gx<=q.xMax() and q.yMin()<=gy<=q.yMax() for l,q in pin.getGeometries())
            target(layer,gx,gy,('PREFERRED_PIN_ACCESS',pin.getInst().getName(),pin.getMTerm().getName()))
    choices.sort();unique=[];seen=set()
    for row in choices:
        key=tuple(row[1:4])
        if key not in seen:seen.add(key);unique.append(row)
        if len(unique)==12:break
    assert unique
    rows.append({'diode':name,'net':n,'access_points':points,'closest_preserved_segments':unique})
out=C/'reports/antenna_stub_full_targets.json';assert not out.exists()
out.write_text(json.dumps({'read_only':True,'scope':'Actual preserved wire segment projections, existing native via centers covered by metal and geometry-validated original preferred pin accesses. No inferred terminal coordinate.','diodes':rows},indent=2)+'\n')
print('FULL_NATIVE_COPPER_TARGETS',[(r['diode'],r['closest_preserved_segments'][0][:4]) for r in rows],flush=True)
