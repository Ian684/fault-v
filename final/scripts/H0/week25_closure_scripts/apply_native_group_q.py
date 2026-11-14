from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');source=Path('/runtime_final/native_group_p.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=json.loads((C/'reports/native_group_p/result.json').read_text());assert sha(source)==proof['output_sha256']
plan=json.loads((C/'reports/m_li1_closure_wide_plan.json').read_text());assert plan['source_rule_markers']==23 and plan['minimum_rectangle_dimension_dbu']==170
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
prior_dr=json.loads((C/'reports/native_group_p_independent.json').read_text());assert prior_dr['odb_sha256']==sha(source) and prior_dr['unresolved_count']==0
groups=defaultdict(list)
for row in plan['patches']:
    assert row['layer']=='li1';q=row['box_dbu'];assert len(q)==4 and all(x%5==0 for x in q) and q[2]-q[0]>=170 and q[3]-q[1]>=170
    groups[row['net']].append(q)
assert set(groups).isdisjoint({'net6033','_10658_','net6330'}), 'The P/M LI1 equivalence guard would not apply'
for name,boxes in groups.items():
    n=b.findNet(name);assert n and str(n.getSigType()) in ('SIGNAL','CLOCK') and n.getWire();original=primitives(n.getWire())[0]
    e=odb.dbWireEncoder();e.append(n.getWire())
    for x1,y1,x2,y2 in boxes:e.newPath(db.getTech().findLayer('li1'),'ROUTED');e.addPoint(x1,y1);e.addRect(0,0,x2-x1,y2-y1)
    e.end();assert primitives(n.getWire())[0]==original+Counter(('R','li1',*q) for q in boxes)
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
assert {n:v for n,v in wires(b).items() if n not in groups}=={n:v for n,v in oldw.items() if n not in groups}
out=C/'reports/native_group_q';out.mkdir(exist_ok=False)
antenna=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final/native_group_q.odb');target=C/'inputs/native_group_q.odb';assert not native.exists() and not target.exists();odb.write_db(db,str(native))
with native.open('rb') as f,target.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(native)==sha(target)
(out/'result.json').write_text(json.dumps({'output_sha256':sha(native),'source_route_sha256':sha(source),'source_GDS_sha256':plan['source_GDS_sha256'],'actual_GDS_closure_plan':'reports/m_li1_closure_wide_plan.json','LI1_rectangles_added':len(plan['patches']),'minimum_patch_rectangle_dimension_nm':170,'nets':sorted(groups),'antenna_nets':antenna,'passive_diodes_added':20,'cells_graph_PG_guides_obstructions_unchanged':True,'all_unaffected_wire_bytes_preserved':True,'accepted_for_final':False,'scope':'Actual-GDS same-owner LI1 notch closure, carried back into regular routed copper. Fresh full/context DRC/connectivity, full GDS DRC, core LVS and three-RC STA remain required.'},indent=2)+'\n')
print('LI1_CLOSURE_PHYSICAL_CANDIDATE',sha(native),'antenna',antenna,flush=True)
