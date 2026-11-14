"""Read-only primitive and pin geometry around the seven confirmed shorts."""
from pathlib import Path
import json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
C=Path('/work/week25_closure');db,b=load('/runtime/focus_final.odb');tech=db.getTech()
check=json.loads((C/'reports/focus_finish_independent.json').read_text());result=[]
def overlaps(a,z):return a[0]<=z[2] and a[2]>=z[0] and a[1]<=z[3] and a[3]>=z[1]
for m in check['unresolved']:
    box=m['bbox_dbu'];roi=[box[0]-1500,box[1]-1500,box[2]+1500,box[3]+1500];row={'marker':m,'nets':{}}
    import re
    for name in re.findall(r'net:([^\s]+)',m['srcs']):
        net=b.findNet(name);shapes=[]
        for q in primitives(net.getWire())[0]:
            if q[0]=='S':
                half=tech.findLayer(q[1]).getWidth()//2
                bounds=[min(q[2],q[4])-half,min(q[3],q[5])-half,max(q[2],q[4])+half,max(q[3],q[5])+half]
            elif q[0] in ('T','V'):
                v=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);r=v.getBBox();bounds=[r.xMin()+q[2],r.yMin()+q[3],r.xMax()+q[2],r.yMax()+q[3]]
            else:bounds=list(q[2:6])
            if overlaps(bounds,roi):shapes.append(q)
        pins=[]
        for t in net.getITerms():
            gs=[(l.getName(),[r.xMin(),r.yMin(),r.xMax(),r.yMax()]) for l,r in t.getGeometries()]
            if any(overlaps(g[1],roi) for g in gs):pins.append({'pin':t.getInst().getName()+'/'+t.getMTerm().getName(),'geometry':gs})
        row['nets'][name]={'shapes':shapes,'pins_in_ROI':pins}
    result.append(row)
(C/'reports/remaining_short_geometry.json').write_text(json.dumps(result,indent=2)+'\n')
for r in result:
    print(r['marker']['srcs'],r['marker']['layer'],r['marker']['bbox_dbu'],flush=True)
    for n,v in r['nets'].items():print(n,v,flush=True)
