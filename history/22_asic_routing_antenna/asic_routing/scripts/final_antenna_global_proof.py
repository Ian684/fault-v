"""Verify zero global overflow for the exact final cell/diode placement and graph."""
from pathlib import Path
import ast,datetime,hashlib,json,struct,sys,odb
R=Path('/work/routing');tag,g,mode=sys.argv[1:];assert all(v.replace('_','').isalnum() for v in [tag,g]) and mode in ['prepare','verify']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'obstructions','wires'})]:
    tree=ast.parse((R/'scripts'/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
def load(p):
    db=odb.dbDatabase.create();odb.read_db(db,str(p));return db,db.getChip().getBlock()
source=R/'runs'/tag/'final/odb/fault_v_asic_top.odb';metrics=json.loads((source.parents[1]/'metrics.json').read_text());assert metrics['route__drc_errors']==metrics['route__antenna_violation__count']==0
d,b=load(source);identity=fixed(b);obs=obstructions(b)
receipt=R/'reports'/f'{g}_input.json'
if mode=='prepare':
    assert not receipt.exists()
    for n in b.getNets():
        if n.getWire():odb.dbWire.destroy(n.getWire())
    assert fixed(b)==identity and obstructions(b)==obs and not wires(b)
    target=R/'inputs'/f'{g}.odb';assert not target.exists();odb.write_db(d,str(target))
    state={'odb':'/work/routing/'+target.relative_to(R).as_posix(),'metrics':{}}
    for key in ['nl','pnl','sdc','json_h','vh']:
        paths=list((source.parents[1]/key).glob('*'));assert len(paths)==1
        state[key]='/work/routing/'+paths[0].relative_to(R).as_posix()
    (R/f'{g}_state.json').write_text(json.dumps(state,indent=2)+'\n')
    c=json.loads((R/'config_antenna_drive_global.json').read_text());assert c['GRT_ANTENNA_REPAIR_ITERS']==0 and not c['GRT_ALLOW_CONGESTION']
    (R/f'config_{g}.json').write_text(json.dumps(c,indent=2)+'\n')
    a={'pass':True,'source':source.relative_to(R).as_posix(),'source_sha256':sha(source),'input':target.relative_to(R).as_posix(),'input_sha256':sha(target),'identical_final_cells_graph_PG_obstructions':True,'scope':'Remove only detailed wires in a clone; actual accepted-candidate routing is unchanged. This global proof uses all final protection diodes and the resized driver.'}
    receipt.write_text(json.dumps(a,indent=2)+'\n')
else:
    original_receipt=receipt.read_bytes();original_receipt_sha=sha(receipt)
    a=json.loads(receipt.read_text());assert a['source_sha256']==sha(source)
    checks=json.loads((R/'reports'/g/'global_checks.json').read_text());assert checks['pass'] and checks['total_overflow']==0
    result=R/'runs'/g/'final/odb/fault_v_asic_top.odb';gd,gb=load(result);assert sha(result)==checks['odb_sha256']
    assert fixed(gb)==identity and obstructions(gb)==obs
    a.update(final_global_verified=True,global_source_odb_sha256=sha(result),total_overflow=0)
    snapshot=R/'reports'/f'{g}_input_before_verification.json';assert not snapshot.exists();snapshot.write_bytes(original_receipt)
    assert sha(snapshot)==original_receipt_sha
    launch_path=R/'reports'/f'{g}_launch.json';launch=json.loads(launch_path.read_text())
    name=receipt.relative_to(R).as_posix();assert launch['sha256'][name]==original_receipt_sha
    receipt.write_text(json.dumps(a,indent=2)+'\n')
    launch['sha256'].update({name:sha(receipt),snapshot.relative_to(R).as_posix():original_receipt_sha})
    launch['verification_receipt_snapshot']=snapshot.relative_to(R).as_posix()
    launch['verification_finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    launch_path.write_text(json.dumps(launch,indent=2)+'\n')
print(json.dumps(a,indent=2))
