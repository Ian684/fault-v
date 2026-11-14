"""Bind final routing to reviewed cells, passive additions and exact PG geometry."""
from pathlib import Path
import hashlib,json,re,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,obstructions,path_type
from reviewed_drivers import load_driver_review
C=Path('/work/week25_closure');tag=sys.argv[1];assert re.fullmatch('[a-z0-9_]+',tag)
runtime_name=sys.argv[2] if len(sys.argv)>2 else 'final_route.odb';output=sys.argv[3] if len(sys.argv)>3 else 'final_route_invariants.json'
assert re.fullmatch('[a-z0-9_]+\.odb',runtime_name) and Path(output).name==output
source=Path('/runtime')/runtime_name;reference=Path('/runtime_final/antenna_ready.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
pair=json.loads((C/'runs'/tag/'1-openroad-detailedrouting/native_pair.json').read_text());assert pair['native_DRC']==pair['antenna_nets']==0 and sha(source)==pair['odb_sha256']
assert sha(reference)==json.loads((C/'reports/antenna_access.json').read_text())['output_sha256']
db,b=load(source);rd,rb=load(reference);expected=fixed(rb);relocations=[]
if fixed(b)!=expected:
    reviews=[]
    for file in (C/'reports').glob('native_group_*/result.json'):
        review=json.loads(file.read_text())
        if review.get('output_sha256')==sha(source) and review.get('only_added_passive_diode_locations_changed'):reviews.append((file,review))
    assert len(reviews)==1,'A changed placement needs one exact-source passive-diode review'
    file,review=reviews[0];relocations=review['only_added_passive_diode_locations_changed']
    assert {r['diode'] for r in relocations}=={'ANTENNA_7559','ANTENNA_7560','ANTENNA_7567','ANTENNA_7572'} and len(relocations)==4
    assert review['placement_response'].startswith('0 ') and review['all_original_cells_graph_PG_guides_obstructions_unchanged']
    cells=dict(expected[0])
    for row in relocations:
        old=cells[row['diode']]
        assert old[0]==row['master']=='sky130_fd_sc_hd__diode_2' and old[1]==row.get('old_orientation',row['orientation']) and list(old[2])==row['old_location']
        assert row['local_native_DRC']==0 and row['same_phase_and_empty_native_row_slot']
        assert b.findInst(row['diode']).findITerm('DIODE').getNet().getName()==row['net']
        assert row['orientation'] in ('R0','MX')
        cells[row['diode']]=(old[0],row['orientation'],tuple(row['new_location']),old[3])
    expected=(cells,expected[1],expected[2])
assert fixed(b)==expected and obstructions(b)==obstructions(rb)
count=sum(n.getWire() is not None for n in b.getNets());assert count==41337
assert all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
targets,_=load_driver_review(C)
for name,row in targets.items():assert b.findInst(name).getMaster().getName()==row['master']
(C/'reports'/output).write_text(json.dumps({'source_sha256':sha(source),'reference_prepared_sha256':sha(reference),'cells_graph_PG_and_obstructions_unchanged':not relocations,'all_original_cells_graph_PG_and_obstructions_unchanged':True,'reviewed_added_passive_diode_relocations':relocations,'regular_routed_nets':count,'reviewed_driver_count':len(targets),'all_reviewed_driver_masters_preserved':True,'all_routes_status_ROUTED':True,'scope':'Native same-model binding only; final filler/GDS/DRC/LVS/RCX/STA/activity/IR/density gates remain required.'},indent=2)+'\n')
print('FINAL_ROUTE_INVARIANTS_VERIFIED',count,sha(source),flush=True)
