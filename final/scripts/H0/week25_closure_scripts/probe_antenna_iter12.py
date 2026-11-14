from pathlib import Path
import hashlib,json,sys
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed
C=Path('/work/week25_closure');source=Path('/native/drt_iter12.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
digest=sha(source);t=Tech();design=Design(t);design.readDb(str(source));b=design.getDb().getChip().getBlock()
rd,rb=load('/runtime_final/antenna_ready.odb');assert fixed(b)==fixed(rb)
antenna=int(design.evalTclString('check_antennas -report_file /work/week25_closure/reports/antenna_iter12_antenna.rpt'))
assert sha(source)==digest
(C/'reports/antenna_iter12_probe.json').write_text(json.dumps({'source_sha256':digest,'antenna_nets':antenna,'cells_graph_PG_unchanged':True,'accepted_for_final':False,'scope':'Completed immutable iteration snapshot only. Independent native/context DRC and every physical connected component still required.'},indent=2)+'\n')
print('ANTENNA_ITER12_PROBE',digest,'antenna',antenna,flush=True)
