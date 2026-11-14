from pathlib import Path
import hashlib,json,odb
C=Path('/work/week25_closure');source=C/'inputs/pg_via_trial.odb'
plan=json.loads((C/'reports/pg_via_plan.json').read_text())
with source.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==plan['output_sha256']
db=odb.dbDatabase.create();odb.read_db(db,str(source));b=db.getChip().getBlock()
lookup={}
for name in ('VPWR','VGND'):
    for sw in b.findNet(name).getSWires():
        for box in sw.getWires():
            if box.isVia():lookup[name,*box.getViaXY()]=box
for r in plan['planned_replacements']:
    box=lookup[r['net'],*r['new_xy']];v=box.getBlockVia()
    assert v.getName()==r['new_via'] and sum(q.getTechLayer().getName()=='via4' for q in v.getBoxes())==8
target=C/'inputs/pg_via_trial.def';assert not target.exists();odb.write_def(b,str(target))
state=json.loads((C/'pg_ir_state.json').read_text());state['def']=str(target);state['metrics']={};state.pop('spef',None)
(C/'pg_stream_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_trim_check.json').read_text());(C/'config_pg_stream.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('Serialized PG arrays re-read with eight actual cuts each; native DEF exported.',flush=True)
