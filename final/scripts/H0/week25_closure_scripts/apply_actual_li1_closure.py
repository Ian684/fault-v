from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');source=Path('/runtime_final/antenna_jumper.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=json.loads((C/'reports/antenna_jumper/result.json').read_text());assert sha(source)==proof['output_sha256']
plan=json.loads((C/'reports/li1_closure_plan.json').read_text());assert len(plan['patches'])==57
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
groups=defaultdict(list)
for row in plan['patches']:
    assert row['layer']=='li1';q=row['box_dbu'];assert len(q)==4 and all(x%5==0 for x in q) and q[0]<q[2] and q[1]<q[3]
    groups[row['net']].append(q)
for name,boxes in groups.items():
    n=b.findNet(name);assert n and str(n.getSigType()) in ('SIGNAL','CLOCK') and n.getWire();original=primitives(n.getWire())[0]
    e=odb.dbWireEncoder();e.append(n.getWire())
    for x1,y1,x2,y2 in boxes:e.newPath(db.getTech().findLayer('li1'),'ROUTED');e.addPoint(x1,y1);e.addRect(0,0,x2-x1,y2-y1)
    e.end();assert primitives(n.getWire())[0]==original+Counter(('R','li1',*q) for q in boxes)
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
assert {n:v for n,v in wires(b).items() if n not in groups}=={n:v for n,v in oldw.items() if n not in groups}
out=C/'reports/li1_spacing';out.mkdir(exist_ok=False)
antenna=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final/li1_spacing.odb');target=C/'inputs/li1_spacing.odb';assert not native.exists() and not target.exists();odb.write_db(db,str(native))
with native.open('rb') as f,target.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(native)==sha(target)
(out/'result.json').write_text(json.dumps({'output_sha256':sha(native),'source_route_sha256':sha(source),'source_GDS_sha256':plan['source_GDS_sha256'],'actual_GDS_closure_plan':'reports/li1_closure_plan.json','LI1_rectangles_added':len(plan['patches']),'nets':sorted(groups),'antenna_nets':antenna,'passive_diodes_added':20,'cells_graph_PG_guides_obstructions_unchanged':True,'all_unaffected_wire_bytes_preserved':True,'accepted_for_final':False,'scope':'Actual-GDS same-owner LI1 notch closure, carried back into regular routed copper. Fresh full/context DRC/connectivity, full GDS DRC, core LVS and three-RC STA remain required.'},indent=2)+'\n')
print('LI1_CLOSURE_PHYSICAL_CANDIDATE',sha(native),'antenna',antenna,flush=True)
