"""Reroute a complete conflict cover without locking neighboring signal routes."""
from pathlib import Path
import hashlib,json,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,path_type
C=Path('/work/week25_closure');source=Path('/runtime/focus_reference.odb')
proof=json.loads((C/'reports/focus_route_input.json').read_text())
with source.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==proof['reference_sha256']
db,b=load(source);before=fixed(b);old_wires=wires(b);old_guides=guides(b);old_obs=obstructions(b)
assert len(old_wires)==41337 and all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
dirty=proof['editable_nets'];assert len(dirty)==75
for name in dirty:
    net=b.findNet(name);assert net and net.getWire();odb.dbWire.destroy(net.getWire())
retained={n:v for n,v in old_wires.items() if n not in dirty}
assert wires(b)==retained and len(retained)==41262
assert fixed(b)==before and guides(b)==old_guides and obstructions(b)==old_obs
target=C/'inputs/focus_unfixed.odb';assert not target.exists();odb.write_db(db,str(target))
state=json.loads((C/'focus_route_state.json').read_text());state.update(odb='/runtime/focus_unfixed.odb',metrics={})
for key in ('spef','gds','klayout_gds','def'):state.pop(key,None)
(C/'focus_unfixed_state.json').write_text(json.dumps(state,indent=2)+'\n')
script=(C/'scripts/cached_detailed.tcl').read_text().replace('detailed_route -no_pin_access','detailed_route -or_seed 7 -no_pin_access').replace('-droute_end_iter 64','-droute_end_iter 32')
(C/'scripts/focus_unfixed_detailed.tcl').write_text(script)
cli=(C/'scripts/cached_route_cli.py').read_text().replace('scripts/cached_detailed.tcl','scripts/focus_unfixed_detailed.tcl')
(C/'scripts/focus_unfixed_cli.py').write_text(cli)
audit=(C/'scripts/audit_cached_pins.py').read_text().replace("C/'inputs/cached_guided.odb'","Path('/runtime/focus_unfixed.odb')").replace('reports/cached_all_pins.json','reports/focus_unfixed_all_pins.json')
assert '/runtime/focus_unfixed.odb' in audit
(C/'scripts/audit_focus_unfixed_pins.py').write_text(audit)
with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
(C/'reports/focus_unfixed_input.json').write_text(json.dumps({'accepted':False,'source_sha256':proof['reference_sha256'],'derived_sha256':digest,'cleared_nets':dirty,'retained_routes':len(retained),'all_retained_wire_bytes_exact':True,'all_routes_status_ROUTED':True,'cells_graph_PG_guides_obstructions_unchanged':True,'scope':'75-net conflict-cover retry on complete 50-driver checkpoint. All neighbors remain editable ROUTED; native preferred APs retained and must pass a fresh geometry audit. Source has real DRVs; fresh final checks mandatory.'},indent=2)+'\n')
print('FOCUS_UNFIXED_READY',len(dirty),'dirty',len(retained),'native ROUTED routes retained',flush=True)
