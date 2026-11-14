"""Clear a small complete cover of independently confirmed shorts; retain all other bytes."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,path_type
C=Path('/work/week25_closure');source=Path('/runtime/focus_unfixed_final.odb')
check=json.loads((C/'reports/focus_unfixed_independent.json').read_text())
with source.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==check['odb_sha256']
assert check['unresolved_count']==7 and all(m['type']=='Short' for m in check['unresolved'])
db,b=load(source);before=fixed(b);old=wires(b);g=guides(b);obs=obstructions(b)
assert len(old)==41337 and all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
edges={tuple(sorted(set(re.findall(r'net:([^\s]+)',m['srcs'])))) for m in check['unresolved']}
assert len(edges)==5 and all(len(e)==2 for e in edges)
cost={}
for name in {n for e in edges for n in e}:
    n=b.findNet(name);assert n and n.getWire() and g[name] and str(n.getSigType())=='SIGNAL'
    length=sum((abs(q[4]-q[2])+abs(q[5]-q[3]))*count for q,count in primitives(n.getWire())[0].items() if q[0]=='S')
    cost[name]=(len(n.getITerms())+len(n.getBTerms()),length,name)
dirty={min(e,key=lambda n:cost[n]) for e in edges}
assert len(dirty)==5 and all(dirty.intersection(e) for e in edges)
assert not all(set().intersection(e) for e in edges)
connectivity=json.loads((C/'reports/focus_unfixed_all_connectivity.json').read_text())
assert connectivity['source_sha256']==check['odb_sha256'] and not connectivity['missing_wires']
assert [r['net'] for r in connectivity['bad_nets']]==['net3116']
dirty.add('net3116');assert len(dirty)==6
for name in dirty:odb.dbWire.destroy(b.findNet(name).getWire())
assert wires(b)=={n:v for n,v in old.items() if n not in dirty}
assert fixed(b)==before and guides(b)==g and obstructions(b)==obs
target=Path('/runtime_final/short_cover_b.odb');out=C/'inputs/short_cover_b.odb'
assert not target.exists() and not out.exists();odb.write_db(db,str(target))
import shutil
with target.open('rb') as inp,out.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
with target.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
with out.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
state=json.loads((C/'runs/focus_unfixed_a/1-openroad-detailedrouting/state_out.json').read_text())
state.update(odb=str(target),metrics={})
for k in ('gds','klayout_gds','spef','def'):state.pop(k,None)
(C/'short_cover_b_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_focus_route.json').read_text());cfg.update(DRT_THREADS=4,DRT_OPT_ITERS=32)
(C/'config_short_cover_b.json').write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/short_cover_b_input.json').write_text(json.dumps({'accepted':False,'source_sha256':check['odb_sha256'],'derived_sha256':digest,'cleared_nets':sorted(dirty),'conflict_edges':sorted(edges),'costs':cost,'inherited_disconnected_net_also_cleared':'net3116','all_other_wire_bytes_cells_graph_PG_guides_obstructions_unchanged':True},indent=2)+'\n')
print('SHORT_COVER_READY',sorted(dirty),digest,flush=True)
