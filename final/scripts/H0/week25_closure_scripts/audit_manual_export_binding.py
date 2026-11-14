from pathlib import Path
import hashlib,json,re,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure');tag=sys.argv[1] if len(sys.argv)>1 else 'signal_manual_a';drname=sys.argv[2] if len(sys.argv)>2 else 'signal_gap_independent.json';output=sys.argv[3] if len(sys.argv)>3 else 'manual_export_binding.json'
assert re.fullmatch('[a-z0-9_]+',tag) and Path(drname).name==drname and Path(output).name==output
run=C/'runs'/tag/'1-openroad-detailedrouting'
source=run/'native_final.odb';state=json.loads((run/'state_out.json').read_text());exported=Path(state['odb'])
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
pair=json.loads((run/'native_pair.json').read_text());dr=json.loads((C/'reports'/drname).read_text());assert sha(source)==pair['odb_sha256']==dr['odb_sha256'] and pair['native_DRC']==dr['unresolved_count']==0
db,b=load(source);rd,rb=load(exported)
assert fixed(b)==fixed(rb) and wires(b)==wires(rb) and guides(b)==guides(rb) and obstructions(b)==obstructions(rb)
record={'native_final_sha256':sha(source),'exported_ODB_sha256':sha(exported),'all_exported_cells_graph_PG_wire_bytes_guides_obstructions_equal_checked_source':True,'DRC_authority':'independent full/context native geometry check, not an uninitialized router counter','fresh_view_sha256':{key:sha(Path(state[key])) for key in ('nl','pnl','def')}}
(C/'reports'/output).write_text(json.dumps(record,indent=2)+'\n');print('EXACT_MANUAL_EXPORT_BINDING_VERIFIED',record['native_final_sha256'],flush=True)
