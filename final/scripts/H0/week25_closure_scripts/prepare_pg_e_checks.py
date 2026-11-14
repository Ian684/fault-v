"""Bind the compact-array candidate to unchanged circuit geometry and fresh export/IR checks."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure');source=Path('/runtime_final/pg_compact_e.odb');prior=Path('/runtime/pg_via_d.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
trial=json.loads((C/'reports/pg_compact_e/result.json').read_text());dr=json.loads((C/'reports/pg_e_independent.json').read_text())
assert sha(source)==trial['output_sha256']==dr['odb_sha256'] and dr['unresolved_count']==0
assert sha(prior)==trial['source_sha256'] and len(trial['accepted_changes'])==5
db,b=load(source);rd,rb=load(prior)
before=fixed(rb);after=fixed(b)
assert before[:2]==after[:2] and wires(b)==wires(rb) and guides(b)==guides(rb) and obstructions(b)==obstructions(rb)
def via(block,net,xy):
    found=[q for sw in block.findNet(net).getSWires() for q in sw.getWires() if q.isVia() and tuple(q.getViaXY())==tuple(xy)]
    assert len(found)==1;return found[0]
removed=Counter();added=Counter()
for row in trial['accepted_changes']:
    old=via(rb,row['net'],row['prior_xy']);new=via(b,row['net'],row['new_xy'])
    assert old.getBlockVia().getName()==row['prior_via'] and new.getBlockVia().getName()==row['new_via']
    assert sum(q.getTechLayer().getName()=='via4' for q in new.getBlockVia().getBoxes())==8
    for counter,q in ((removed,old),(added,new)):counter[(row['net'],q.xMin(),q.yMin(),q.xMax(),q.yMax(),q.getBlockVia().getName())]+=1
assert Counter(after[2])==Counter(before[2])-removed+added
native=source.with_suffix('.def');dest=C/'inputs/pg_compact_e.def';assert not native.exists() and not dest.exists();odb.write_def(b,str(native))
with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(dest)
state=json.loads((C/'pg_d_stream_state.json').read_text());state.update(odb=str(source),def_=None,metrics={});state.pop('def_',None);state['def']=str(native)
(C/'pg_e_stream_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_working.json').read_text());cfg['meta']={'version':2,'flow':['KLayout.StreamOut','KLayout.DRC']}
assert cfg['KLAYOUT_CONFLICT_RESOLUTION']=='OverwriteCell' and any('dedup' in p for p in cfg['MACROS']['sky130_sram_2kbyte_1rw1r_32x512_8']['gds'])
(C/'config_pg_e_stream.json').write_text(json.dumps(cfg,indent=2)+'\n')
state=json.loads((C/'pg_d_ir_state.json').read_text());state.update(odb=str(source),metrics={})
(C/'pg_e_ir_state.json').write_text(json.dumps(state,indent=2)+'\n')
(C/'reports/runtime_pg_compact_e_odb.json').write_text(json.dumps({'source':str(C/'inputs/pg_compact_e.odb'),'runtime':str(source),'sha256':sha(source),'bytes':source.stat().st_size},indent=2)+'\n')
(C/'reports/pg_e_geometry_binding.json').write_text(json.dumps({'source_sha256':sha(prior),'output_sha256':sha(source),'independent_DRC':0,'only_five_planned_PG_arrays_changed':True,'all_cells_graph_signal_wire_bytes_guides_obstructions_preserved':True,'all_five_arrays_retain_eight_cuts':True,'fresh_DEF_sha256':sha(native),'accepted_for_final':False,'scope':'Native geometry binding only. Fresh GDS/LVS and controlled IR/EM still required.'},indent=2)+'\n')
print('PG_E_CHECK_INPUTS_VERIFIED',sha(source),flush=True)
