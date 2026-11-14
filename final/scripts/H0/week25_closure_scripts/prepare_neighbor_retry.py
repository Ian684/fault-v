"""Rip up measured neighboring fixed routes touched by the enlarged/repositioned drivers."""
from pathlib import Path
import ast,hashlib,json,re,shutil,struct,time,odb
C=Path('/work/week25_closure');R=Path('/work/routing')
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','guides','guide_sig','obstructions'})]:
    tree=ast.parse((R/'scripts'/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
folder=C/'runs/minimal_route_a/1-openroad-detailedrouting'
snapshots=sorted([p for p in folder.glob('drt_iter*.odb') if time.time()-p.stat().st_mtime>20],key=lambda p:p.stat().st_mtime_ns)
assert len(snapshots)>=2;source=snapshots[-2]
reports=sorted(folder.glob('fault_v_asic_top.drc-*.rpt'),key=lambda p:p.stat().st_mtime_ns)[-3:]
assert reports
names=set();report_identity={}
for report in reports:
    text=report.read_text();names.update(re.findall(r'\bnet:([^\s]+)',text))
    report_identity[report.name]=hashlib.sha256(report.read_bytes()).hexdigest()
assert len(names)>10
digest=hashlib.sha256(source.read_bytes()).hexdigest()
frozen=C/'inputs/neighbor_source.odb';assert not frozen.exists();shutil.copyfile(source,frozen)
assert hashlib.sha256(frozen.read_bytes()).hexdigest()==digest
db=odb.dbDatabase.create();odb.read_db(db,str(frozen));b=db.getChip().getBlock()
global_state=json.loads((C/'runs/minimal_global_a/1-openroad-globalrouting/state_out.json').read_text())
gd=odb.dbDatabase.create();odb.read_db(gd,global_state['odb']);gb=gd.getChip().getBlock()
identity=fixed(b);obs=obstructions(b);before=wires(b)
assert fixed(gb)==identity and obstructions(gb)==obs
cleared=[];power=[]
for name in sorted(names):
    net=b.findNet(name);assert net is not None,name
    if str(net.getSigType()) in ('POWER','GROUND'):power.append(name);continue
    if net.getWire():odb.dbWire.destroy(net.getWire());cleared.append(name)
retained={n:d for n,d in before.items() if n not in cleared}
assert wires(b)==retained
expected=guides(gb)
for net in b.getNets():
    for guide in list(net.getGuides()):odb.dbGuide.destroy(guide)
    for layer,via,box,congested,connected,jumper in expected[net.getName()]:
        guide=odb.dbGuide_create(net,db.getTech().findLayer(layer),db.getTech().findLayer(via),odb.Rect(*box),congested);assert guide
        guide.setIsConnectedToTerm(connected);guide.setIsJumper(jumper)
assert fixed(b)==identity and obstructions(b)==obs and wires(b)==retained and guides(b)==expected
target=C/'inputs/neighbor_guided.odb';assert not target.exists();odb.write_db(db,str(target))
state={key:global_state[key] for key in ('nl','pnl','sdc','json_h','vh')};state.update(odb=str(target),metrics={})
(C/'route_neighbor_state.json').write_text(json.dumps(state,indent=2)+'\n')
proof={'accepted':False,'source_snapshot':source.name,'source_sha256':digest,'report_sha256':report_identity,'measured_violating_nets':sorted(names),'cleared_signal_nets':cleared,'PG_nets_left_intact':power,'retained_exact_routes':len(retained),'cells_graph_PG_preserved':True,'all_guides_match_zero_overflow_source':True,'reason':'Retained old routes are fixed obstacles for native DRT; driver growth/moves can collide with nonincident neighboring routes. Rip up all measured source nets, not only the changed cell terminals.'}
(C/'reports/neighbor_input.json').write_text(json.dumps(proof,indent=2)+'\n')
print(json.dumps(proof,indent=2),flush=True)
