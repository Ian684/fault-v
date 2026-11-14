"""Apply only full-GDS-screened PG changes; preserve every cell and regular wire."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure');source=Path('/runtime/pg_via_b.odb')
planfile=C/(sys.argv[1] if len(sys.argv)>1 else 'reports/pg_c_plan.json');prefix=sys.argv[2] if len(sys.argv)>2 else 'pg_c';basename=sys.argv[3] if len(sys.argv)>3 else 'pg_via_c'
assert prefix.replace('_','').isalnum() and basename.replace('_','').isalnum()
plan=json.loads(planfile.read_text());assert plan['geometry_screen_pass']
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==plan['source_ODB_sha256']
db,b=load(source);before=fixed(b);old_wires=wires(b);old_guides=guides(b);old_obs=obstructions(b)
def rect(q):return [q.xMin(),q.yMin(),q.xMax(),q.yMax()]
removed=[];added=[]
for row in plan['via_changes']:
    a,z=row['before'],row['after'];net=b.findNet(row['net'])
    matches=[(sw,q) for sw in net.getSWires() for q in sw.getWires() if q.isVia() and list(q.getViaXY())==a['new_xy']]
    assert len(matches)==1
    sw,old=matches[0];assert old.getBlockVia().getName()==a['new_via']
    via=b.findVia(z['new_via']);assert via and sum(q.getTechLayer().getName()=='via4' for q in via.getBoxes())==8
    removed.append((row['net'],*rect(old),a['new_via']))
    new=odb.dbSBox.create(sw,via,*z['new_xy'],str(old.getWireShapeType()));assert new
    assert rect(new)==z['new_bbox'];added.append((row['net'],*rect(new),z['new_via']));odb.dbSBox.destroy(old)
groups=defaultdict(list)
for row in plan['wire_patches']:
    x1,y1,x2,y2=row['box'];groups[row['net'],x1,x2].append((y1,y2))
merged=[]
for (net,x1,x2),intervals in groups.items():
    result=[]
    for y1,y2 in sorted(intervals):
        if result and y1<=result[-1][1]:result[-1][1]=max(result[-1][1],y2)
        else:result.append([y1,y2])
    for y1,y2 in result:
        layer=db.getTech().findLayer('met4');sw=next(iter(b.findNet(net).getSWires()))
        q=odb.dbSBox.create(sw,layer,x1,y1,x2,y2,'STRIPE');assert q and rect(q)==[x1,y1,x2,y2]
        added.append((net,x1,y1,x2,y2,'met4'));merged.append({'net':net,'box':[x1,y1,x2,y2]})
after=fixed(b)
assert before[:2]==after[:2] and wires(b)==old_wires and guides(b)==old_guides and obstructions(b)==old_obs
assert Counter(before[2])-Counter(after[2])==Counter(removed) and Counter(after[2])-Counter(before[2])==Counter(added)
out=C/'inputs'/(basename+'.odb');assert not out.exists();odb.write_db(db,str(out));odb.write_def(b,str(out.with_suffix('.def')))
plan.update(output_ODB_sha256=sha(out),merged_M4_patches=merged,all_cells_signal_graph_routes_guides_obstructions_unchanged=True,only_planned_PG_changes=True,accepted=False)
((C/'reports')/(prefix+'_applied.json')).write_text(json.dumps(plan,indent=2)+'\n')
state=json.loads((C/'pg_ir_state_c.json').read_text());state['odb']='/runtime/'+basename+'.odb';state['spef']={'nom_*':'/runtime/baseline.nom.spef'};state['metrics']={}
(C/(prefix+'_ir_state.json')).write_text(json.dumps(state,indent=2)+'\n')
state=json.loads((C/'pg_stream_state_c.json').read_text());state['odb']='/runtime/'+basename+'.odb';state['def']='/runtime/'+basename+'.def';state['metrics']={}
(C/(prefix+'_stream_state.json')).write_text(json.dumps(state,indent=2)+'\n')
print('PG_C_APPLIED',len(plan['via_changes']),'compact arrays',len(merged),'merged M4 patches; signal geometry unchanged',flush=True)
