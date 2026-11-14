"""Release the blocking M2 neighbors together, retaining the accepted local gap patch."""
from pathlib import Path
import hashlib,json,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,path_type
C=Path('/work/week25_closure');source=Path('/runtime_final/wide_notch_b.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=json.loads((C/'reports/wide_notch_b/result.json').read_text());assert sha(source)==proof['output_sha256'] and proof['remaining_local_markers']==2 and len(proof['accepted_patch'])==1
conn=json.loads((C/'reports/wide_b_all_connectivity.json').read_text());assert conn['source_sha256']==proof['source_sha256'] and conn['all_signal_geometry_connected']
db,b=load(source);before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
dirty={'net4985','net8601','net6342','net4469'}
region=(1575000,620000,1630000,662000);added=[]
for name in sorted(dirty|{'_09360_'}):
    n=b.findNet(name);assert n and str(n.getSigType())=='SIGNAL' and n.getWire() and oldg[name]
    for layer in ('met1','met2','met3','met4','met5'):
        l=db.getTech().findLayer(layer);q=odb.dbGuide_create(n,l,l,odb.Rect(*region),False);assert q
        q.setIsConnectedToTerm(False);q.setIsJumper(False);added.append({'net':name,'layer':layer,'box':region})
for name in dirty:odb.dbWire.destroy(b.findNet(name).getWire())
assert fixed(b)==before and obstructions(b)==oldo and wires(b)=={n:v for n,v in oldw.items() if n not in dirty}
assert all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
for name,values in guides(b).items():
    expected=tuple(sorted(oldg[name]+tuple((r['layer'],r['layer'],tuple(r['box']),False,False,False) for r in added if r['net']==name)))
    assert values==expected
native=Path('/runtime_final/coupled_short_ready.odb');dest=C/'inputs/coupled_short_ready.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(dest)
state=json.loads((C/'runs/wide_polish_b/1-openroad-detailedrouting/state_out.json').read_text());state.update(odb=str(native),metrics={})
for k in ('gds','klayout_gds','spef','def'):state.pop(k,None)
(C/'coupled_short_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_short_polish.json').read_text());cfg.update(DRT_THREADS=8,DRT_OPT_ITERS=8)
(C/'config_coupled_short.json').write_text(json.dumps(cfg,indent=2)+'\n')
tcl=(C/'scripts/short_polish_swapped.tcl').read_text().replace('-droute_end_iter 12','-droute_end_iter 8').replace('SHORT_POLISH_SWAPPED_FINAL','COUPLED_SHORT_FINAL')
p=C/'scripts/coupled_short.tcl';assert not p.exists();p.write_text(tcl)
p=C/'scripts/coupled_short_cli.py';assert not p.exists();p.write_text((C/'scripts/short_polish_swapped_cli.py').read_text().replace('short_polish_swapped.tcl','coupled_short.tcl'))
(C/'reports/coupled_short_input.json').write_text(json.dumps({'source_sha256':sha(source),'derived_sha256':sha(native),'input_local_markers':2,'input_full_DRC_acceptance':False,'cleared_signal_nets':sorted(dirty),'added_guides':added,'all_cells_graph_PG_obstructions_and_other_wire_bytes_preserved':True,'same_net_gap_patch_retained':True,'accepted':False,'scope':'Four actual interacting signal nets released together, including M2 blocking neighbors identified from real copper. Native final DRC, all-net connectivity and complete downstream gates remain mandatory.'},indent=2)+'\n')
print('COUPLED_SHORT_READY',sorted(dirty),sha(native),flush=True)
