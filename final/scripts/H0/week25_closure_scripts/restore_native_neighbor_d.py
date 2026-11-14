"""Try restoring the single remaining blocking neighbor, retaining all other reroutes."""
from pathlib import Path
import hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure');source=Path('/runtime_final/native_group_b.odb');reference=Path('/runtime/antenna_native12.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==json.loads((C/'reports/native_group_b/result.json').read_text())['output_sha256']
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();rd,rb=load(reference)
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b);out=C/'reports/native_group_d';out.mkdir(exist_ok=False)
net=b.findNet('net6170');odb.dbWire.destroy(net.getWire());w=odb.dbWire.create(net);w.append(rb.findNet('net6170').getWire())
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
assert {n:v for n,v in wires(b).items() if n!='net6170'}=={n:v for n,v in oldw.items() if n!='net6170'}
design.evalTclString('set_thread_count 2');p=out/'local.drc.rpt'
design.evalTclString('drt::check_drc -box {1570000 630000 1600000 652000} -output_file '+str(p)+' -marker_name RestoreNeighbor')
text=p.read_text();count=text.count('violation type:');print('RESTORED_NEIGHBOR_LOCAL_DRC',count,flush=True)
assert count==0,'Restored neighbor is not locally clean'
ant=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final/native_group_d.odb');dest=C/'inputs/native_group_d.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as f,dest.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(native)==sha(dest)
(out/'result.json').write_text(json.dumps({'source_sha256':sha(source),'reference_sha256':sha(reference),'output_sha256':sha(native),'restored_net':'net6170','local_DRC':count,'antenna_nets':ant,'all_other_wire_bytes_and_cells_graph_PG_guides_obstructions_preserved':True,'accepted_for_final':False,'scope':'Local eligibility only. Full independent native/context DRC and connectivity are required; remaining antenna must also close.'},indent=2)+'\n')
print('RESTORED_NEIGHBOR_D_READY',ant,sha(native),flush=True)
