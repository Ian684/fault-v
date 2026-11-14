"""Retain eight cuts while compacting five PG arrays that cross signal metal."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import fixed,wires,guides,obstructions
C=Path('/work/week25_closure');source=Path('/runtime/pg_via_d.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=json.loads((C/'reports/pg_d_independent.json').read_text());assert sha(source)==proof['odb_sha256'] and proof['unresolved_count']==6
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock()
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
out=C/'reports/pg_compact_e';out.mkdir(exist_ok=False);design.evalTclString('set_thread_count 2')
compact=b.findVia('W25_PG_VIA4_2_4_190_190_310_310');assert compact and sum(q.getTechLayer().getName()=='via4' for q in compact.getBoxes())==8
base=json.loads((C/'reports/pg_via_plan_b.json').read_text())['planned_replacements']
changes={(r['net'],*r['before']['old_xy']):r['after'] for r in json.loads((C/'reports/pg_d_applied.json').read_text())['via_changes']}
rows=[changes.get((r['net'],*r['old_xy']),r) for r in base]
selected=[]
for row in rows:
    a,c,z,f=row['new_bbox']
    if any(m['srcs'].startswith('net:'+row['net']+' ') and a<m['bbox_dbu'][2] and z>m['bbox_dbu'][0] and c<m['bbox_dbu'][3] and f>m['bbox_dbu'][1] for m in proof['unresolved']):selected.append(row)
assert len(selected)==5
def check(box,tag):
    design.getTritonRoute().clearDesign();p=out/(tag+'.rpt');design.evalTclString(f'drt::check_drc -box {{{" ".join(map(str,box))}}} -output_file {p} -marker_name PGCompactTrial')
    text=p.read_text();rows=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(rows)==text.count('violation type:');return Counter(rows)
accepted=[];attempts=[]
for index,row in enumerate(selected):
    net=b.findNet(row['net']);matches=[(sw,q) for sw in net.getSWires() for q in sw.getWires() if q.isVia() and tuple(q.getViaXY())==tuple(row['new_xy'])]
    assert len(matches)==1;sw,old=matches[0];oldvia=old.getBlockVia();oldxy=tuple(old.getViaXY());shape=str(old.getWireShapeType())
    x,y=row['old_xy'];box=[x-20000,y-20000,x+20000,y+20000];current=check(box,f'{index}_baseline')
    # Every trial uses the same real eight-cut PDK-rule-generated master.
    options=[0,1620,1700,-1620,-1700,3400,-3400,5100,-5100,6800,-6800]
    for k,dy in enumerate(options):
        odb.dbSBox.destroy(old);newxy=(x,y+dy);new=odb.dbSBox.create(sw,compact,*newxy,shape);assert new
        observed=check(box,f'{index}_{k}');ok=not(observed-current) and sum(observed.values())<sum(current.values())
        attempt={'net':row['net'],'old_xy':row['old_xy'],'candidate_xy':newxy,'baseline_markers':sum(current.values()),'markers':sum(observed.values()),'accepted':ok};attempts.append(attempt);print('PG_COMPACT_ATTEMPT',attempt,flush=True)
        if ok:
            accepted.append({'net':row['net'],'prior_xy':oldxy,'prior_via':oldvia.getName(),'new_xy':newxy,'new_via':compact.getName(),'cuts':8,'old_original_xy':row['old_xy'],'remaining_local_markers':sum(observed.values())});break
        odb.dbSBox.destroy(new);old=odb.dbSBox.create(sw,oldvia,*oldxy,shape);assert old
    assert fixed(b)[:2]==before[:2] and wires(b)==oldw and guides(b)==oldg and obstructions(b)==oldo
    (out/'progress.json').write_text(json.dumps({'accepted':False,'attempts':attempts,'accepted_changes':accepted},indent=2)+'\n')
native=Path('/runtime_final/pg_compact_e.odb');dest=C/'inputs/pg_compact_e.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(dest)
record={'accepted':False,'source_sha256':sha(source),'output_sha256':sha(native),'attempts':attempts,'accepted_changes':accepted,'all_signal_wire_bytes_cells_graph_guides_obstructions_preserved':True,'all_modified_arrays_retain_eight_cuts':True,'scope':'Strict no-new-local-marker PG geometry trial. Full independent native/context DRC, full-GDS core LVS, stream audits and fresh controlled IR/EM are mandatory before promotion.'}
(out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('PG_COMPACT_TRIAL_COMPLETE',len(accepted),sha(native),flush=True)
