"""Reuse the calibrated FIXED protection, then require exact normalization before acceptance."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,encode_fixed,path_type,restore_exact
import odb
C=Path('/work/week25_closure');source=C/'inputs/cached_guided.odb'
db,b=load(source);rd,rb=load(source)
before=(fixed(b),wires(b),guides(b),obstructions(b));protected=[]
for net in b.getNets():
    if not net.getWire():continue
    assert path_type(net.getWire())=='ROUTED' and net.getNonDefaultRule() is None
    geometry=primitives(net.getWire())[0]
    encode_fixed(net.getWire(),geometry,db.getTech(),b);net.setWireType('FIXED')
    assert primitives(net.getWire())[0]==geometry and path_type(net.getWire())=='FIXED'
    protected.append(net.getName())
assert len(protected)==40305
assert fixed(b)==before[0] and guides(b)==before[2] and obstructions(b)==before[3]
target=C/'inputs/protected_guided.odb';assert not target.exists();odb.write_db(db,str(target))
restore_exact(b,rb,protected)
assert (fixed(b),wires(b),guides(b),obstructions(b))==before
state=json.loads((C/'cached_route_state.json').read_text());state.update(odb=str(target),metrics={})
(C/'protected_route_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_cached_route.json').read_text());(C/'config_protected_route.json').write_text(json.dumps(cfg,indent=2)+'\n')
record={'accepted':False,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'protected_nets':protected,'protected_routes':len(protected),'temporary_status_only':True,'all_protected_primitive_geometry_exact':True,'normalization_roundtrip_all_wire_bytes_exact':True,'cells_graph_PG_guides_obstructions_unchanged':True,'scope':'Only 1032 previously cleared nets can be routed. Native pin_access is regenerated with the protected geometry present. FIXED metadata must be restored to original ROUTED bytes and fresh independent full-chip DRC performed; no filtered fixed-shape report is accepted as final.'}
(C/'reports/protected_route_input.json').write_text(json.dumps(record,indent=2)+'\n')
print('PROTECTED_ROUTE_READY',len(protected),flush=True)
