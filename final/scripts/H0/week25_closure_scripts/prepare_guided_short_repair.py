"""Extend only the four remaining conflict nets' local guides; preserve every copper byte."""
from pathlib import Path
import hashlib,json,re,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure');source=Path('/runtime/signal_polished.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
dr=json.loads((C/'reports/wide_b_independent.json').read_text());cn=json.loads((C/'reports/wide_b_all_connectivity.json').read_text())
assert sha(source)==dr['odb_sha256']==cn['source_sha256'] and dr['unresolved_count']==3 and cn['all_signal_geometry_connected']
db,b=load(source);before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
names={n for row in dr['unresolved'] for n in re.findall(r'net:([^\s]+)',row['srcs'])}-{'VPWR','VGND'}
assert names=={'net9703','_09360_','net4985','net6342'}
region=(1575000,620000,1630000,662000);added=[]
for row in dr['unresolved']:
    a,c,z,f=row['bbox_dbu'];assert region[0]<a<z<region[2] and region[1]<c<f<region[3]
for name in sorted(names):
    n=b.findNet(name);assert n.getWire() and str(n.getSigType())=='SIGNAL'
    for layer in ('met1','met2','met3','met4','met5'):
        l=db.getTech().findLayer(layer);q=odb.dbGuide_create(n,l,l,odb.Rect(*region),False);assert q
        q.setIsConnectedToTerm(False);q.setIsJumper(False);added.append({'net':name,'layer':layer,'box':region})
afterg=guides(b)
assert fixed(b)==before and wires(b)==oldw and obstructions(b)==oldo
for name in oldg:
    expected=tuple(sorted(oldg[name]+tuple((r['layer'],r['layer'],tuple(r['box']),False,False,False) for r in added if r['net']==name)))
    assert afterg[name]==expected,('Unplanned guide change',name)
native=Path('/runtime_final/guided_short_ready.odb');dest=C/'inputs/guided_short_ready.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(dest)
state=json.loads((C/'runs/wide_polish_b/1-openroad-detailedrouting/state_out.json').read_text());state.update(odb=str(native),metrics={})
for k in ('gds','klayout_gds','spef','def'):state.pop(k,None)
(C/'guided_short_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_short_polish.json').read_text());cfg['DRT_THREADS']=4
(C/'config_guided_short.json').write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/guided_short_input.json').write_text(json.dumps({'source_sha256':sha(source),'output_sha256':sha(native),'input_independent_DRC':3,'all_41337_signal_nets_connected':True,'all_cells_graph_PG_wire_bytes_and_obstructions_unchanged':True,'only_added_guides':added,'accepted':False,'scope':'Broaden real repair-worker routing space where current copper has left original GRT guides. No metal, AP or rule changes in this preparation; all routed output gates remain required.'},indent=2)+'\n')
print('GUIDED_SHORT_INPUT_READY',len(added),sha(native),flush=True)
