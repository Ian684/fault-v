"""Fit five spacing-conflicting PG arrays back inside their original landing areas."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure');source=C/'inputs/pg_via_trial.odb'
plan=json.loads((C/'reports/pg_via_plan.json').read_text())
db,b=load(source);before=fixed(b);old_wires=wires(b);old_guides=guides(b);old_obs=obstructions(b)
def rect(q):return (q.xMin(),q.yMin(),q.xMax(),q.yMax())
markers=json.loads((C/'reports/pg_stream_a_markers.json').read_text());assert len(markers)==5
selected=[]
for marker in markers:
    assert marker['category']=="'m5.2'"
    points=[tuple(map(float,v)) for v in re.findall(r'([0-9.]+),([0-9.]+)',marker['values'][0])]
    bbox=[round(min(p[0] for p in points)*1000),round(min(p[1] for p in points)*1000),round(max(p[0] for p in points)*1000),round(max(p[1] for p in points)*1000)]
    hits=[r for r in plan['planned_replacements'] if r['new_top_box'][0]<=bbox[2] and r['new_top_box'][2]>=bbox[0] and r['new_top_box'][1]<=bbox[3] and r['new_top_box'][3]>=bbox[1]]
    assert len(hits)==1,(bbox,len(hits));selected.append(hits[0])
assert len({(r['net'],*r['new_xy']) for r in selected})==5
removed=[];added=[]
for r in selected:
    net=b.findNet(r['net']);matches=[(sw,q) for sw in net.getSWires() for q in sw.getWires() if q.isVia() and list(q.getViaXY())==r['new_xy']]
    assert len(matches)==1
    sw,box=matches[0];old=box.getBlockVia();assert old.getName()==r['new_via']
    name='W25_PG_VIA4_2_2_190_190_310_310';v=b.findVia(name)
    if v is None:
        v=odb.dbVia.create(b,name);p=odb.dbViaParams();prior=old.getViaParams()
        props=('BottomLayer','CutLayer','TopLayer','NumCutCols','NumCutRows','XCutSize','YCutSize','XCutSpacing','YCutSpacing','XOrigin','YOrigin','XBottomEnclosure','YBottomEnclosure','XTopEnclosure','YTopEnclosure','XBottomOffset','YBottomOffset','XTopOffset','YTopOffset')
        for prop in props:getattr(p,'set'+prop)(getattr(prior,'get'+prop)())
        p.setNumCutCols(2);p.setNumCutRows(2);v.setViaGenerateRule(old.getViaGenerateRule());v.setViaParams(p)
    assert sum(q.getTechLayer().getName()=='via4' for q in v.getBoxes())==4
    assert r['stress_current_A']<.00249
    removed.append((r['net'],*rect(box),old.getName()))
    x,y=r['old_xy'];new=odb.dbSBox.create(sw,v,x,y,str(box.getWireShapeType()));assert new
    added.append((r['net'],*rect(new),name));odb.dbSBox.destroy(box)
    r.update(prior_trial_xy=r['new_xy'],prior_trial_via=r['new_via'],new_xy=[x,y],new_via=name,new_bbox=rect(new),cols=2,rows=2,new_cut_count=4)
    for layer,key in [('met4','new_bottom_box'),('met5','new_top_box')]:
        z=next(q for q in v.getBoxes() if q.getTechLayer().getName()==layer);r[key]=[x+z.xMin(),y+z.yMin(),x+z.xMax(),y+z.yMax()]
    assert r['new_bottom_box'][0]>=r['old_bbox'][0] and r['new_bottom_box'][1]>=r['old_bbox'][1] and r['new_bottom_box'][2]<=r['old_bbox'][2] and r['new_bottom_box'][3]<=r['old_bbox'][3]
after=fixed(b)
assert before[:2]==after[:2] and wires(b)==old_wires and guides(b)==old_guides and obstructions(b)==old_obs
assert Counter(before[2])-Counter(after[2])==Counter(removed) and Counter(after[2])-Counter(before[2])==Counter(added)
for r in plan['planned_replacements']:r.setdefault('new_cut_count',8)
target=C/'inputs/pg_via_b.odb';assert not target.exists();odb.write_db(db,str(target))
with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
plan.update(output_sha256=digest,total_new_cuts=sum(r['new_cut_count'] for r in plan['planned_replacements']),spacing_repaired_sites=5,accepted=False)
(C/'reports/pg_via_plan_b.json').write_text(json.dumps(plan,indent=2)+'\n')
target_def=C/'inputs/pg_via_b.def';assert not target_def.exists();odb.write_def(b,str(target_def))
state=json.loads((C/'pg_ir_state.json').read_text());state['odb']=str(target);state['metrics']={}
(C/'pg_ir_state_b.json').write_text(json.dumps(state,indent=2)+'\n')
state['def']=str(target_def);state.pop('spef',None)
(C/'pg_stream_state_b.json').write_text(json.dumps(state,indent=2)+'\n')
print('PG_B_READY',len(plan['planned_replacements']),plan['total_new_cuts'],'cuts; five smaller real arrays',flush=True)
