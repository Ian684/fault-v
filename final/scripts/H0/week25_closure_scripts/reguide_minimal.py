from pathlib import Path
import ast,hashlib,json,struct,re,odb
C=Path('/work/week25_closure');R=Path('/work/routing')
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','guides','guide_sig','obstructions'})]:
    tree=ast.parse((R/'scripts'/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
load=lambda p:json.loads(p.read_text())
record=load(C/'reports/minimal_input.json');state=load(C/'runs/minimal_global_a/1-openroad-globalrouting/state_out.json')
log=(C/'runs/minimal_global_a/1-openroad-globalrouting/openroad-globalrouting.log').read_text()
rows=re.findall(r'Total\s+(\d+)\s+(\d+)\s+([0-9.]+)%\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)',log)
assert rows and 'GRT-0115' not in log
overflow=list(map(int,rows[-1][-3:]));assert overflow==[0,0,0],overflow
def database(path):
    db=odb.dbDatabase.create();odb.read_db(db,str(path));return db,db.getChip().getBlock()
source=C/'inputs/minimal_partial.odb'
assert hashlib.sha256(source.read_bytes()).hexdigest()==record['partial_sha256']
db,b=database(source);gd,gb=database(state['odb'])
identity=fixed(b);obs=obstructions(b);retained=wires(b)
assert fixed(gb)==identity and obstructions(gb)==obs
assert retained==record['retained_wire_sha256']
expected=guides(gb)
for net in b.getNets():
    for guide in list(net.getGuides()):odb.dbGuide.destroy(guide)
    for layer,via,box,congested,connected,jumper in expected[net.getName()]:
        q=odb.dbGuide_create(net,db.getTech().findLayer(layer),db.getTech().findLayer(via),odb.Rect(*box),congested)
        assert q
        q.setIsConnectedToTerm(connected);q.setIsJumper(jumper)
assert guides(b)==expected and fixed(b)==identity and obstructions(b)==obs and wires(b)==retained
target=C/'inputs/minimal_guided.odb';assert not target.exists();odb.write_db(db,str(target))
clean={k:state[k] for k in ('nl','pnl','sdc','json_h','vh')};clean.update(odb=str(target),metrics={})
(C/'route_state.json').write_text(json.dumps(clean,indent=2)+'\n')
cfg=load(C/'config_global.json');cfg['meta']={'version':2,'flow':['OpenROAD.DetailedRouting']}
cfg.update(DRT_THREADS=4,DRT_OPT_ITERS=64,DRT_ANTENNA_REPAIR_ITERS=0)
(C/'config_route.json').write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/guided_input.json').write_text(json.dumps({'global_overflow':overflow,'retained_exact_routes':len(retained),'cleared_routes':len(record['cleared_nets']),'guided_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'matching_cells_graph_PG_and_guides':True,'accepted':False},indent=2)+'\n')
print('Matching zero-overflow guides installed; retained',len(retained),'native routes.',flush=True)
