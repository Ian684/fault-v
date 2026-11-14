"""Normalize one completed immutable router iteration; never read an active .1 file."""
from pathlib import Path
import hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,restore_exact,path_type
C=Path('/work/week25_closure');iteration=int(sys.argv[1]);stem=sys.argv[2]
assert 0<=iteration<=20 and re.fullmatch(r'native_group_[c-z]',stem)
source=Path('/runtime_final/native_group_b_snapshots')/('drt_iter'+str(iteration)+'.odb');reference=Path('/runtime/antenna_native12.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
source_sha=sha(source);assert source.stat().st_size>500000000
assert sha(reference)==json.loads((C/'reports/antenna_iter12_probe.json').read_text())['source_sha256']
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();rd,rb=load(reference)
assert fixed(b)==fixed(rb) and guides(b)==guides(rb) and obstructions(b)==obstructions(rb)
dirty=set(json.loads((C/'reports/native_group_b/input.json').read_text())['editable_nets'])
protected=[n.getName() for n in rb.getNets() if n.getWire() and n.getName() not in dirty]
restore_exact(b,rb,protected);oldw=wires(rb);after=wires(b)
assert len(protected)==41331 and len(after)==41337 and all(after[n]==oldw[n] for n in protected)
assert all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
out=C/'reports'/stem;out.mkdir(exist_ok=False)
ant=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final')/(stem+'.odb');dest=C/'inputs'/(stem+'.odb');assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as f,dest.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(native)==sha(dest) and sha(source)==source_sha
(out/'result.json').write_text(json.dumps({'source_snapshot':str(source),'source_snapshot_sha256':source_sha,'reference_sha256':sha(reference),'output_sha256':sha(native),'editable_nets':sorted(dirty),'protected_routes':len(protected),'protected_wire_bytes_exactly_restored':True,'cells_graph_PG_guides_obstructions_unchanged':True,'antenna_nets':ant,'accepted_for_final':False,'scope':'Completed iteration only; temporary FIXED statuses removed by exact-source byte restoration. Full independent native/context DRC, physical connectivity and downstream final gates remain required.'},indent=2)+'\n')
print('NORMALIZED_NATIVE_SNAPSHOT_READY',stem,iteration,ant,sha(native),flush=True)
