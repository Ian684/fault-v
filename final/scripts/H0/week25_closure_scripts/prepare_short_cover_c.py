"""Retry both participants of each remaining crossing from the connected B result."""
from pathlib import Path
import hashlib,json,re,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,path_type
C=Path('/work/week25_closure');source=Path('/route_b/1-openroad-detailedrouting/native_final.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
dr=json.loads((C/'reports/short_b_final_independent.json').read_text());cn=json.loads((C/'reports/short_b_final_all_connectivity.json').read_text())
assert sha(source)==dr['odb_sha256']==cn['source_sha256'] and dr['unresolved_count']==4 and cn['all_signal_geometry_connected']
dirty={n for r in dr['unresolved'] for n in re.findall(r'net:([^\s]+)',r['srcs'])}
assert dirty=={'_09360_','net4985','_03544_','_03545_','net4469','net6342'}
db,b=load(source);before=fixed(b);old=wires(b);g=guides(b);obs=obstructions(b)
for name in dirty:
    n=b.findNet(name);assert n and str(n.getSigType())=='SIGNAL' and n.getWire() and g[name];odb.dbWire.destroy(n.getWire())
assert wires(b)=={n:v for n,v in old.items() if n not in dirty} and fixed(b)==before and guides(b)==g and obstructions(b)==obs
assert all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
target=Path('/runtime_final/short_cover_c.odb');out=C/'inputs/short_cover_c.odb';assert not target.exists() and not out.exists();odb.write_db(db,str(target))
with target.open('rb') as inp,out.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(target)==sha(out)
state=json.loads((C/'runs/short_cover_b/1-openroad-detailedrouting/state_out.json').read_text());state.update(odb=str(target),metrics={})
for k in ('gds','klayout_gds','spef','def'):state.pop(k,None)
(C/'short_cover_c_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_short_cover_b.json').read_text());cfg.update(DRT_THREADS=8,DRT_OPT_ITERS=12)
(C/'config_short_cover_c.json').write_text(json.dumps(cfg,indent=2)+'\n')
tcl=(C/'scripts/short_cover_b.tcl').read_text().replace('set_thread_count 4','set_thread_count 8').replace('-or_seed 7','-or_seed 19').replace('-droute_end_iter 32','-droute_end_iter 12').replace('SHORT_COVER_B_FINAL','SHORT_COVER_C_FINAL')
for name,code in [('short_cover_c.tcl',tcl),('short_cover_c_cli.py',(C/'scripts/short_cover_b_cli.py').read_text().replace('short_cover_b.tcl','short_cover_c.tcl'))]:
    p=C/'scripts'/name;assert not p.exists();p.write_text(code)
(C/'reports/short_cover_c_input.json').write_text(json.dumps({'accepted':False,'source_sha256':sha(source),'derived_sha256':sha(target),'cleared_nets':sorted(dirty),'both_participants_of_each_confirmed_short_cleared':True,'all_other_wire_bytes_cells_graph_PG_guides_obstructions_unchanged':True,'seed':19,'threads':8,'iterations':12},indent=2)+'\n')
print('SHORT_COVER_C_READY',sorted(dirty),sha(target),flush=True)
