from pathlib import Path
import json,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
C=Path('/work/week25_closure');result={};roi=[1582000,638000,1586000,642000]
hit=lambda q:q[0]<=roi[2] and q[2]>=roi[0] and q[1]<=roi[3] and q[3]>=roi[1]
for tag in ('native_group_b','native_group_c'):
    db,b=load('/runtime_final/'+tag+'.odb');tech=db.getTech();record={}
    for name in ('net3347','net5547','net6170','net4319'):
        rows=[]
        for q in primitives(b.findNet(name).getWire())[0]:
            if q[0]=='S':
                h=tech.findLayer(q[1]).getWidth()//2
                if hit([q[2]-h,q[3]-h,q[4]+h,q[5]+h]):rows.append(q)
            elif q[0]=='R' and hit(q[2:6]):rows.append(q)
            elif q[0] in ('T','V') and roi[0]-1000<=q[2]<=roi[2]+1000 and roi[1]-1000<=q[3]<=roi[3]+1000:rows.append(q)
        record[name]=rows
    result[tag]=record;odb.dbDatabase.destroy(db)
p=C/'reports/native_group_crossing_shapes.json';assert not p.exists();p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
