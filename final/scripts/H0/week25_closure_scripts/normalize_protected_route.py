"""Restore every protected wire byte, then bind fresh checks to the normalized database."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,restore_exact,path_type
import odb
C=Path('/work/week25_closure')
state=json.loads((C/'runs/protected_route_a/1-openroad-detailedrouting/state_out.json').read_text())
source=Path(state['odb']);record=json.loads((C/'reports/protected_route_input.json').read_text())
ref=C/'inputs/cached_guided.odb';assert hashlib.sha256(ref.read_bytes()).hexdigest()==record['source_sha256']
db,b=load(source);rd,rb=load(ref);before=fixed(b)
assert fixed(rb)==before and obstructions(b)==obstructions(rb)
restore_exact(b,rb,record['protected_nets'])
assert fixed(b)==before
after=wires(b);original=wires(rb)
for name in record['protected_nets']:assert after[name]==original[name]
assert len(after)==41337 and all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
target=C/'inputs/protected_normalized.odb';assert not target.exists();odb.write_db(db,str(target))
state.update(odb=str(target),metrics={})
# All downstream geometry is regenerated; stale GDS/SPEF must not survive this state.
for key in ('gds','klayout_gds','spef','def'):state.pop(key,None)
(C/'post_route_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_working.json').read_text())
cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','KLayout.StreamOut','KLayout.DRC','Magic.SpiceExtraction','Netgen.LVS','OpenROAD.CheckAntennas','OpenROAD.RCX']}
cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc'
(C/'config_post_route.json').write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/protected_normalization.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'normalized_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'all_protected_wire_bytes_exact':True,'protected_routes':len(record['protected_nets']),'all_routes_status_ROUTED':True,'cells_graph_PG_unchanged':True,'total_wired_nets':len(after),'accepted':False,'scope':'Temporary FIXED metadata removed. Fresh independent all-geometry DRC, electrical, antenna, extraction and LVS gates still required.'},indent=2)+'\n')
print('NORMALIZED_PROTECTED_ROUTE',len(after),'wired nets',flush=True)
