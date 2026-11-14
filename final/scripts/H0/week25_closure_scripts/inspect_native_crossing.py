from pathlib import Path
import json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
C=Path('/work/week25_closure');db,b=load('/runtime/antenna_native12.odb');tech=db.getTech();roi=[1582500,638000,1585500,641000]
hit=lambda q:q[0]<=roi[2] and q[2]>=roi[0] and q[1]<=roi[3] and q[3]>=roi[1]
record={}
for name in ('net3347','net5547'):
    n=b.findNet(name);rows=[]
    for q in primitives(n.getWire())[0]:
        if q[0]=='S':
            h=tech.findLayer(q[1]).getWidth()//2;box=[min(q[2],q[4])-h,min(q[3],q[5])-h,max(q[2],q[4])+h,max(q[3],q[5])+h]
            if hit(box):rows.append(q)
        elif q[0] in ('T','V'):
            if roi[0]-1000<=q[2]<=roi[2]+1000 and roi[1]-1000<=q[3]<=roi[3]+1000:
                v=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);rows.append({'via':q,'boxes':[(z.getTechLayer().getName(),z.xMin(),z.yMin(),z.xMax(),z.yMax()) for z in v.getBoxes()]})
    record[name]=rows
out=C/'reports/native_crossing_shapes.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
