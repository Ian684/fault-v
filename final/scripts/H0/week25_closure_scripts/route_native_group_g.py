"""Reroute the measured crossing neighborhood; restore every protected byte."""
from pathlib import Path
import hashlib,json,sys,shutil,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,encode_fixed,path_type,restore_exact
C=Path('/work/week25_closure');source=Path('/runtime_final/native_group_c.odb')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)==json.loads((C/'reports/native_group_c/result.json').read_text())['output_sha256']
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
rd,rb=load(source);before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
dirty={'net3347','net5547','net4319','net6170','net2682','net8704','net3311','net3177','net4842'}
added_guides=[]
for name in sorted(dirty):
    n=b.findNet(name)
    for layer in ('met1','met2','met3','met4','met5'):
        l=tech.findLayer(layer);box=[1568000,622000,1615000,669000]
        g=odb.dbGuide_create(n,l,l,odb.Rect(*box),False);assert g
        g.setIsConnectedToTerm(False);g.setIsJumper(False)
        added_guides.append({'net':name,'layer':layer,'bbox_dbu':box})
oldg=guides(b)
out=C/'reports/native_group_g';out.mkdir(exist_ok=False);protected=[]
for n in b.getNets():
    if not n.getWire():continue
    if n.getName() in dirty:continue
    g=primitives(n.getWire())[0];encode_fixed(n.getWire(),g,tech,b);n.setWireType('FIXED')
    assert primitives(n.getWire())[0]==g;protected.append(n.getName())
assert len(protected)==41337-len(dirty) and fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
(out/'input.json').write_text(json.dumps({'source_sha256':sha(source),'editable_nets':sorted(dirty),'protected_routes':len(protected),'all_initial_routes_retained':True,'native_pin_access_regenerated':True,'added_local_escape_guides':added_guides,'accepted_for_final':False},indent=2)+'\n')
print('MEASURED_NEIGHBORHOOD_READY',len(dirty),len(protected),flush=True)
design.evalTclString('set_thread_count 4')
design.evalTclString('set_debug_level DRT snapshot 1')
Path('/runtime_final/native_group_g_snapshots').mkdir(exist_ok=False)
design.evalTclString('detailed_route_debug -snapshot_dir /runtime_final/native_group_g_snapshots')
reply=design.evalTclString('detailed_route -or_seed 53 -or_k 7 -droute_end_iter 20 -drc_report_iter_step 1 -verbose 1 -output_drc '+str(out/'router.drc'))
print('NATIVE_DETAILED_ROUTE_REPLY',repr(reply),flush=True)
assert reply in ('',None),reply
raw=int(design.evalTclString('detailed_route_num_drvs'))
restore_exact(b,rb,protected)
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
after=wires(b);assert len(after)==41337 and all(after[n]==oldw[n] for n in protected)
assert all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
ant=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final/native_group_g.odb');dest=C/'inputs/native_group_g.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as f,dest.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(native)==sha(dest)
(out/'result.json').write_text(json.dumps({'source_sha256':sha(source),'output_sha256':sha(native),'editable_nets':sorted(dirty),'all_initial_routes_retained':True,'native_pin_access_regenerated':True,'added_local_escape_guides':added_guides,'protected_routes':len(protected),'protected_wire_bytes_exactly_restored':True,'cells_graph_PG_guides_obstructions_unchanged':True,'router_reported_DRC':raw,'antenna_nets':ant,'accepted_for_final':False,'scope':'Temporary protection removed; full native/context DRC and all-net physical connectivity are mandatory before export.'},indent=2)+'\n')
print('NATIVE_GROUP_READY',raw,ant,sha(native),flush=True)
