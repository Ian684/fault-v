"""Keep native diode routes; select coherent original/native neighboring routes."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');source=Path('/native/drt_iter12.odb');original=Path('/runtime_final/focus_pg.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
probe=json.loads((C/'reports/antenna_iter12_probe.json').read_text());assert sha(source)==probe['source_sha256']
proof=json.loads((C/'reports/focus_pg_rebase.json').read_text());assert sha(original)==proof['output_sha256']
cn=json.loads((C/'reports/antenna_iter12_all_connectivity.json').read_text());assert cn['all_signal_geometry_connected'] and cn['source_sha256']==sha(source)
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock()
nd,nb=load(source);od,ob=load(original)
before=fixed(b);oldg=guides(b);oldo=obstructions(b)
native_wires=wires(nb);original_wires=wires(ob);assert set(native_wires)==set(original_wires)
affected=set(json.loads((C/'reports/antenna_access.json').read_text())['diode_affected_nets']);assert len(affected)==18
protected={'net3347','net5547','net2682','net8704'};assert not protected&affected
selected={name:'native' if name in affected else 'original' for name in native_wires}
def assign(name,version):
    ref=nb if version=='native' else ob;net=b.findNet(name)
    if net.getWire():odb.dbWire.destroy(net.getWire())
    wire=odb.dbWire.create(net);wire.append(ref.findNet(name).getWire())
    assert primitives(wire)[0]==primitives(ref.findNet(name).getWire())[0]
    selected[name]=version
for name in native_wires:
    if name not in affected and native_wires[name]!=original_wires[name]:assign(name,'original')
out=C/'reports/antenna_rebase';out.mkdir(exist_ok=False)
design.evalTclString('set_thread_count 2');history=[]
def check(index):
    design.getTritonRoute().clearDesign();p=out/f'planning_{index:02}.rpt'
    design.evalTclString('drt::check_drc -output_file '+str(p)+' -marker_name RouteSelectionPlanning')
    text=p.read_text();rows=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+) on Layer ([^\n]+)',text)
    assert len(rows)==text.count('violation type:')
    # Partition-prone same-net LI1 markers are deferred to the separate full/context gate.
    return [r for r in rows if not (r[3]=='li1' and r[0] in ('NS Metal','Metal Spacing') and len(re.findall(r'net:([^\s]+)',r[1]))==1)]
seen=set()
for iteration in range(24):
    state=tuple(sorted(n for n in selected if selected[n]=='native' and n not in affected));assert state not in seen,'Repeated route-selection state';seen.add(state)
    markers=check(iteration);history.append({'iteration':iteration,'non_partition_planning_markers':len(markers),'native_neighbor_count':len(state),'markers':markers})
    (out/'progress.json').write_text(json.dumps({'history':history,'selected_native_neighbors':state,'accepted_for_final':False},indent=2)+'\n')
    print('ROUTE_SELECTION',iteration,len(markers),'native neighbors',len(state),flush=True)
    if not markers:break
    changes={}
    for kind,src,box,layer in markers:
        names=set(re.findall(r'net:([^\s]+)',src));assert names and all(n in selected for n in names),(kind,src)
        if len(names)==1:
            n=next(iter(names));assert n not in affected and n not in protected,(kind,src,'hard-source marker')
            changes[n]='native' if selected[n]=='original' else 'original';continue
        can_native={n for n in names if n not in protected and n not in affected and selected[n]=='original'}
        if can_native:
            for n in can_native:changes[n]='native'
        else:
            can_original={n for n in names if n not in affected and n not in protected and selected[n]=='native'}
            assert can_original,(kind,src,'Conflicting hard-source routes')
            for n in can_original:changes[n]='original'
    assert changes
    for n,v in changes.items():assign(n,v)
else:raise AssertionError('Route-selection bound reached')
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
actual=wires(b);assert all(actual[n]==(native_wires[n] if v=='native' else original_wires[n]) for n,v in selected.items())
antenna=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final/antenna_rebase.odb');target=C/'inputs/antenna_rebase.odb';assert not native.exists() and not target.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,target.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(target)
(out/'result.json').write_text(json.dumps({'output_sha256':sha(native),'source_native_sha256':probe['source_sha256'],'source_original_sha256':proof['output_sha256'],'antenna_nets':antenna,'passive_diodes_added':20,'native_diode_nets':sorted(affected),'native_neighbor_nets':sorted(n for n,v in selected.items() if v=='native' and n not in affected),'protected_original_nets':sorted(protected),'cells_graph_PG_guides_obstructions_unchanged':True,'every_signal_wire_byte_exact_from_selected_source':True,'accepted_for_final':False,'scope':'Route-selection search only; all raw same-net LI1 markers require the separate independent full/context gate. No DRC waiver or final acceptance.'},indent=2)+'\n')
print('REBASED_NATIVE_ANTENNA_CANDIDATE',sha(native),'antenna',antenna,flush=True)
