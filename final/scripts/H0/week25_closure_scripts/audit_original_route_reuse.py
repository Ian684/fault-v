"""Read-only eligibility check for reusing original clean routes away from all 50 ECO cells."""
from pathlib import Path
import json,re,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
C=Path('/work/week25_closure');db,b=load('/route_b/1-openroad-detailedrouting/drt_iter12.odb');rd,rb=load('/runtime/F.odb')
drivers=set(json.loads((C/'reports/cached_input.json').read_text())['equivalent_drivers']);assert len(drivers)==50
check=json.loads((C/'reports/short_b12_raw.json').read_text());names={n for r in check['markers'] if r['layer']!='li1' for n in re.findall(r'net:([^\s]+)',r['srcs'])}
regions=[]
for name in drivers:
    for block in (b,rb):
        r=block.findInst(name).getBBox();regions.append((r.xMin()-2000,r.yMin()-2000,r.xMax()+2000,r.yMax()+2000))
def hit(q):return any(q[0]<=z and q[2]>=a and q[1]<=f and q[3]>=c for a,c,z,f in regions)
def box(q,tech,block):
    if q[0]=='S':
        h=tech.findLayer(q[1]).getWidth()//2;_,l,x1,y1,x2,y2,e1,e2=q
        return (x1-h,y1-e1,x2+h,y2+e2) if x1==x2 else (x1-e1,y1-h,x2+e2,y2+h)
    if q[0]=='R':return q[2:6]
    v=tech.findVia(q[1]) if q[0]=='T' else block.findVia(q[1]);r=v.getBBox();x,y=q[2:];return (r.xMin()+x,r.yMin()+y,r.xMax()+x,r.yMax()+y)
rows={}
for name in sorted(names):
    n=b.findNet(name);old=rb.findNet(name);assert n and old and n.getWire() and old.getWire()
    terms=lambda v:sorted((p.getInst().getName(),p.getMTerm().getName()) for p in v.getITerms())
    assert terms(n)==terms(old)
    changed_pins=sorted({i for i,p in terms(n)}&drivers)
    orig=primitives(old.getWire())[0];now=primitives(n.getWire())[0]
    touches=any(hit(box(q,rd.getTech(),rb)) for q in orig)
    delta=[]
    for values,tech,block in [(orig-now,rd.getTech(),rb),(now-orig,db.getTech(),b)]:
        boxes=[box(q,tech,block) for q in values]
        delta.append([min(q[0] for q in boxes),min(q[1] for q in boxes),max(q[2] for q in boxes),max(q[3] for q in boxes)] if boxes else None)
    rows[name]={'resized_cell_endpoints':changed_pins,'original_wire_touches_any_old_or_new_ECO_halo':touches,'eligible_for_trial':not changed_pins and not touches,'changed_geometry_bboxes_old_then_new':delta}
    print('ORIGINAL_ROUTE_REUSE',name,rows[name],flush=True)
(C/'reports/original_route_reuse.json').write_text(json.dumps({'read_only':True,'source_snapshot':'short_cover_b completed iteration12','reference':'F.odb, original known clean route','ECO_cells':50,'candidate_nets':rows,'scope':'Eligibility only. No route restored; trials still require all geometry/connectivity/final checks.'},indent=2)+'\n')
