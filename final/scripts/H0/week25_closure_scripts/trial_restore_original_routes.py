"""Trial original clean wires only where endpoints and paths avoid every ECO cell."""
from pathlib import Path
import hashlib,json,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,path_type
C=Path('/work/week25_closure');source=Path('/route_b/1-openroad-detailedrouting/drt_iter12.odb');reference=Path('/runtime/F.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
check=json.loads((C/'reports/short_b12_raw.json').read_text());assert sha(source)==check['source_sha256']
assert sha(reference)=='fe627dd4b1ff4c152dcfa9dd5d08b05c13b7272ab4065d7f0cb8af3d87dd1380'
eligible=json.loads((C/'reports/original_route_reuse.json').read_text())['candidate_nets']
names={n for n,r in eligible.items() if r['eligible_for_trial']};assert 0<len(names)<20
db,b=load(source);rd,rb=load(reference);before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
for name in sorted(names):
    net=b.findNet(name);ref=rb.findNet(name);assert net and ref
    assert not eligible[name]['resized_cell_endpoints'] and not eligible[name]['original_wire_touches_any_old_or_new_ECO_halo']
    odb.dbWire.destroy(net.getWire());wire=odb.dbWire.create(net);wire.append(ref.getWire())
    assert primitives(wire)[0]==primitives(ref.getWire())[0],('Native reference wire did not map exactly',name)
    assert path_type(wire)=='ROUTED'
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
assert {n:v for n,v in wires(b).items() if n not in names}=={n:v for n,v in oldw.items() if n not in names}
target=Path('/runtime_final/original_restore.odb');permanent=C/'inputs/original_restore.odb';assert not target.exists() and not permanent.exists();odb.write_db(db,str(target))
with target.open('rb') as inp,permanent.open('xb') as out:shutil.copyfileobj(inp,out,1024*1024)
digest=sha(target);assert sha(permanent)==digest and sha(source)==check['source_sha256']
(C/'reports/original_restore_input.json').write_text(json.dumps({'source_snapshot_sha256':check['source_sha256'],'original_reference_sha256':sha(reference),'output_sha256':digest,'restored_whole_nets':sorted(names),'all_cells_logical_graph_PG_guides_obstructions_and_other_wire_bytes_preserved':True,'all_restored_primitives_equal_original_clean_route':True,'none_of_the_50_ECO_cells_or_halos_touched':True,'accepted':False,'scope':'Independent geometric trial only; no routing counter accepted. Fresh full native/context DRC, every-net connectivity, antenna and electrical/final gates still required.'},indent=2)+'\n')
print('ORIGINAL_ROUTE_RESTORE_TRIAL',len(names),digest,flush=True)
