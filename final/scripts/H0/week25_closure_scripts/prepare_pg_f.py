"""Remove three GDS-level M5 spacing failures with 0.22um array translations."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure');source=Path('/runtime_final/pg_compact_e.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
e=json.loads((C/'reports/pg_e_geometry_binding.json').read_text());assert sha(source)==e['output_sha256']
counts=json.loads((C/'runs/pg_e_stream_a/2-klayout-drc/reports/drc.klayout.json').read_text());assert {k:v for k,v in counts.items() if v}=={'m5.2':3,'total':3}
db,b=load(source);before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
changes=[('VPWR',(2357470,2216600),-220),('VGND',(902230,3122600),220),('VGND',(1580870,3122600),220)]
removed=Counter();added=Counter();rows=[]
for net,xy,dy in changes:
    found=[(sw,q) for sw in b.findNet(net).getSWires() for q in sw.getWires() if q.isVia() and tuple(q.getViaXY())==xy];assert len(found)==1;sw,old=found[0]
    v=old.getBlockVia();assert v.getName()=='W25_PG_VIA4_2_4_190_190_310_310' and sum(q.getTechLayer().getName()=='via4' for q in v.getBoxes())==8
    removed[(net,old.xMin(),old.yMin(),old.xMax(),old.yMax(),v.getName())]+=1
    newxy=(xy[0],xy[1]+dy);new=odb.dbSBox.create(sw,v,*newxy,str(old.getWireShapeType()));assert new
    added[(net,new.xMin(),new.yMin(),new.xMax(),new.yMax(),v.getName())]+=1;odb.dbSBox.destroy(old)
    rows.append({'net':net,'prior_xy':xy,'new_xy':newxy,'via':v.getName(),'cuts':8,'translation_dbu':[0,dy]})
assert fixed(b)[:2]==before[:2] and Counter(fixed(b)[2])==Counter(before[2])-removed+added
assert wires(b)==oldw and guides(b)==oldg and obstructions(b)==oldo
native=Path('/runtime_final/pg_compact_f.odb');dest=C/'inputs/pg_compact_f.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(dest)
deffile=native.with_suffix('.def');outdef=dest.with_suffix('.def');assert not deffile.exists() and not outdef.exists();odb.write_def(b,str(deffile))
with deffile.open('rb') as inp,outdef.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(deffile)==sha(outdef)
record={'source_sha256':sha(source),'output_sha256':sha(native),'fresh_DEF_sha256':sha(deffile),'only_three_planned_via_translations':rows,'all_signal_wire_bytes_cells_graph_guides_obstructions_preserved':True,'all_three_arrays_retain_eight_cuts':True,'accepted':False,'scope':'0.22um translations address three actual m5.2 GDS failures (1.39um gaps against 1.6um minimum). Fresh native/context and full-GDS DRC, core LVS and controlled IR/EM remain required.'}
(C/'reports/pg_f_geometry_binding.json').write_text(json.dumps(record,indent=2)+'\n')
(C/'reports/runtime_pg_compact_f_odb.json').write_text(json.dumps({'sha256':sha(native),'source':str(dest),'runtime':str(native),'bytes':native.stat().st_size},indent=2)+'\n')
for name in ('stream','ir'):
    state=json.loads((C/f'pg_e_{name}_state.json').read_text());state.update(odb=str(native),metrics={})
    if name=='stream':state['def']=str(deffile)
    (C/f'pg_f_{name}_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_pg_e_stream.json').read_text());(C/'config_pg_f_stream.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('PG_F_ONLY_THREE_ARRAY_TRANSLATIONS',sha(native),flush=True)
