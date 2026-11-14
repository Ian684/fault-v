from pathlib import Path
import ast,hashlib,json,struct,sys,odb
R=Path('/work/routing');tag=sys.argv[1];assert tag.replace('_','').isalnum();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((R/'reports/antenna_model/debug_spacing_20261029/drive_input.json').read_text());assert a['pass']
source=R/a['partial'];global_source=R/'runs'/tag/'final/odb/fault_v_asic_top.odb'
g=json.loads((R/'reports'/tag/'global_checks.json').read_text());assert g['pass'] and g['total_overflow']==0 and sha(global_source)==g['odb_sha256'] and sha(source)==a['partial_sha256']
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','guides','guide_sig','obstructions'})]:
    tree=ast.parse((R/'scripts'/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
def load(p):
    db=odb.dbDatabase.create();odb.read_db(db,str(p));return db,db.getChip().getBlock()
d,b=load(source);gd,gb=load(global_source);identity=fixed(b);obs=obstructions(b);retained=wires(b)
assert identity==fixed(gb) and obs==obstructions(gb) and len(retained)==41333
expected=guides(gb)
for net in b.getNets():
    for q in list(net.getGuides()):odb.dbGuide.destroy(q)
    for layer,via,box,congested,connected,jumper in expected[net.getName()]:
        q=odb.dbGuide_create(net,d.getTech().findLayer(layer),d.getTech().findLayer(via),odb.Rect(*box),congested);assert q
        q.setIsConnectedToTerm(connected);q.setIsJumper(jumper)
assert guides(b)==expected and wires(b)==retained and fixed(b)==identity and obstructions(b)==obs
target=R/'inputs/antenna_drive_native.odb';assert not target.exists();odb.write_db(d,str(target))
state={'odb':'/work/routing/inputs/antenna_drive_native.odb','metrics':{}}
for key in ['nl','pnl','sdc','json_h','vh']:
    paths=list((global_source.parents[1]/key).glob('*'));assert len(paths)==1
    state[key]='/work/routing/'+paths[0].relative_to(R).as_posix()
(R/'antenna_drive_state.json').write_text(json.dumps(state,indent=2)+'\n')
c=json.loads((R/'config_routed_antenna_spacing_20261029_1700.json').read_text());c.update(DRT_THREADS=8,DRT_ANTENNA_REPAIR_ITERS=0)
(R/'config_antenna_drive.json').write_text(json.dumps(c,indent=2)+'\n')
proof={'pass':True,'accepted':False,'source_receipt':'reports/antenna_model/debug_spacing_20261029/drive_input.json','source':a['partial'],'source_sha256':sha(source),'derived':target.relative_to(R).as_posix(),'derived_sha256':sha(target),'global_run':tag,'global_source_sha256':sha(global_source),'global_overflow':0,'retained_exact_wires':41333,'all_guides_match_actual_zero_overflow_source':True,'cleared_whole_nets':a['cleared_whole_nets'],'global_macro_extension_gcells':0,'scope':'One equivalent driver resize, four complete incident nets cleared, all other wires exact; guides from the matching resized circuit and original physical restrictions. Fresh native pin access and all final checks required.'}
(R/'reports/antenna_model/debug_spacing_20261029/drive_guided_input.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
