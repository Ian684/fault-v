"""Try native M1 pin access in place of outside-cell LI1 diode branches."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,encode_fixed
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/runtime/final_route.odb');reference=Path('/runtime_final/focus_pg.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==json.loads((C/'reports/final_route_selection.json').read_text())['source_sha256']
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech();rd,rb=load(reference)
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
raw=(R/'scripts/search_manual_eco.py').read_text();tree=ast.parse(raw);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='normalize_routes'];assert len(nodes)==1;exec(compile(ast.Module(body=nodes,type_ignores=[]),'normalize_routes','exec'))
rows=json.loads((C/'reports/antenna_stubs_h/incomplete.json').read_text())['accepted'];rows += [v for v in json.loads((C/'reports/antenna_stubs_f/result.json').read_text())['accepted'] if v['net']=='net6033'];assert len(rows)==20
ends=defaultdict(set)
for r in rows:
    for p in (r['path'][0]['from'],r['path'][-1]['to']):
        if p[2]==0:ends[r['net']].add(tuple(p[:2]))
v=tech.findVia('L1M1_PR');assert v and v.getBottomLayer().getName()=='li1' and v.getTopLayer().getName()=='met1'
signature=lambda via:tuple(sorted((q.getTechLayer().getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax()) for q in via.getBoxes()))
target_sig=signature(v);changes=[];out=C/'reports/li1_lift_a';out.mkdir(exist_ok=False)
for name,points in ends.items():
    n=b.findNet(name);original=primitives(n.getWire())[0];ref=primitives(rb.findNet(name).getWire())[0];new=original-ref
    li=Counter({q:c for q,c in new.items() if q[0] in ('S','R') and q[1]=='li1'})
    if not li:continue
    removed=li.copy();added=Counter()
    for q,c in new.items():
        if q[0] not in ('T','V'):continue
        via=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1])
        if via.getBottomLayer().getName()=='li1':removed[q]+=c
    for q,c in li.items():
        if q[0]=='S':added['S','met1',*q[2:6],70,70]+=c
    trial=original-removed+added;existing=defaultdict(list)
    for q in trial:
        if q[0] in ('T','V'):
            via=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);existing[q[2],q[3]].append(signature(via))
    for p in sorted(points):
        if target_sig not in existing[p]:trial['T','L1M1_PR',*p]+=1
    encode_fixed(n.getWire(),trial,tech,b);normalize_routes(n.getWire());assert primitives(n.getWire())[0]==trial
    changes.append({'net':name,'LI1_primitives_removed':sum(li.values()),'old_mcon_removed':sum(removed.values())-sum(li.values()),'M1_segments_added':sum(added.values()),'LI1_endpoint_mcon_positions':sorted(points)})
assert len(changes)==18 and fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
changed={r['net'] for r in changes};assert {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in oldw.items() if n not in changed}
design.evalTclString('set_thread_count 2');report=out/'global.drc.rpt'
design.evalTclString('drt::check_drc -output_file '+str(report)+' -marker_name LiftedM1Access')
text=report.read_text();markers=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(markers)==text.count('violation type:')
ant=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
eligible=ant==0 and all(kind in ('NS Metal','Metal Spacing') and src.count('net:')==1 and box.endswith('on Layer li1') for kind,src,box in markers)
record={'source_sha256':sha(source),'reference_sha256':sha(reference),'raw_native_DRC_markers':len(markers),'raw_native_DRC_types':dict(Counter(k for k,s,b in markers)),'antenna_nets':ant,'changes':changes,'all_other_wire_bytes_and_cells_graph_PG_guides_obstructions_preserved':True,'eligible_for_independent_checks':eligible,'accepted_for_final':False,'scope':'Trial lifts only new diode-branch LI1 copper to M1 and retains native mcon endpoints inside original pins. Real native DRC, full GDS LI1 rule replay, connectivity and every final gate are mandatory.'}
if eligible:
    native=Path('/runtime_final/li1_lift_a.odb');dest=C/'inputs/li1_lift_a.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
    with native.open('rb') as f,dest.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
    assert sha(native)==sha(dest);record['output_sha256']=sha(native)
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('M1_ACCESS_LIFT_TRIAL',len(markers),ant,eligible,record.get('output_sha256'),flush=True)
