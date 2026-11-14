"""Restore two low-current original vias and compact one obstructing row-feed stack."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def signature(net,q):
    v=q.getTechVia() or q.getBlockVia() if q.isVia() else None
    return (net,q.xMin(),q.yMin(),q.xMax(),q.yMax(),v.getName() if v else q.getTechLayer().getName())
def compact_stack(b):
    net=b.findNet('VPWR');point=(1610040,633760);newpoint=(1609310,633760)
    via_names={'via3_4_3000_480_1_7_400_400','via2_3_3000_480_1_9_320_320'}
    victims=[]
    for sw in net.getSWires():
        for q in sw.getWires():
            if q.isVia():match=tuple(q.getViaXY())==point and (q.getTechVia() or q.getBlockVia()).getName() in via_names
            else:match=q.getTechLayer().getName()=='met2' and (q.xMin(),q.yMin(),q.xMax(),q.yMax())==(1608630,633575,1611450,633945)
            if match:victims.append((sw,q))
    assert len(victims)==3
    removed=Counter(signature('VPWR',q) for sw,q in victims);added=Counter();metal2=[]
    props=('BottomLayer','CutLayer','TopLayer','NumCutCols','NumCutRows','XCutSize','YCutSize','XCutSpacing','YCutSpacing','XOrigin','YOrigin','XBottomEnclosure','YBottomEnclosure','XTopEnclosure','YTopEnclosure','XBottomOffset','YBottomOffset','XTopOffset','YTopOffset')
    for sw,q in victims:
        if not q.isVia():continue
        old=q.getBlockVia();assert old;prior=old.getViaParams();assert prior.getNumCutRows()==1 and prior.getNumCutCols() in (7,9)
        name='W25_ROWFEED_'+prior.getCutLayer().getName()+'_3';assert not b.findVia(name)
        via=odb.dbVia.create(b,name);params=odb.dbViaParams()
        for prop in props:getattr(params,'set'+prop)(getattr(prior,'get'+prop)())
        params.setNumCutCols(3);via.setViaGenerateRule(old.getViaGenerateRule());via.setViaParams(params)
        assert sum(z.getTechLayer().getName()==prior.getCutLayer().getName() for z in via.getBoxes())==3
        # M1/M3 terminal landing metal stays inside its original connected copper.
        for z in via.getBoxes():
            layer=z.getTechLayer().getName();bounds=(newpoint[0]+z.xMin(),newpoint[1]+z.yMin(),newpoint[0]+z.xMax(),newpoint[1]+z.yMax())
            if layer=='met2':metal2.append(bounds)
            if layer in ('met1','met3'):
                oldboxes=[(point[0]+a.xMin(),point[1]+a.yMin(),point[0]+a.xMax(),point[1]+a.yMax()) for a in old.getBoxes() if a.getTechLayer().getName()==layer]
                assert any(a<=bounds[0] and c<=bounds[1] and z>=bounds[2] and f>=bounds[3] for a,c,z,f in oldboxes)
        new=odb.dbSBox.create(sw,via,*newpoint,str(q.getWireShapeType()));assert new;added[signature('VPWR',new)]+=1
    a=min(q[0] for q in metal2);c=min(q[1] for q in metal2);z=max(q[2] for q in metal2);f=max(q[3] for q in metal2)
    assert 1608630<=a<z<=1610020 and 633575<=c<f<=633945
    sw,strip=next((sw,q) for sw,q in victims if not q.isVia())
    new=odb.dbSBox.create(sw,strip.getTechLayer(),a,c,z,f,str(strip.getWireShapeType()));assert new;added[signature('VPWR',new)]+=1
    for sw,q in victims:odb.dbSBox.destroy(q)
    return removed,added,{'net':'VPWR','prior_site':point,'new_site':newpoint,'cuts_each_interface':3,'original_controlled_current_A':.000004981,'via1_average_capacity_A':.00087,'new_M2_box':(a,c,z,f),'removed_geometry':list(removed.elements()),'added_geometry':list(added.elements()),'scope':'The M1-to-M3 row feed remains connected through three real cuts at each interface. M1/M3 landings stay within original metal, and M2 copper shrinks away from the crossing signal. Fresh actual core LVS and controlled IR/EM remain mandatory.'}
def save(db,b,name,with_def):
    native=Path('/runtime_final')/(name+'.odb');dest=C/'inputs'/(name+'.odb');assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
    with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
    assert sha(native)==sha(dest)
    if with_def:
        p=native.with_suffix('.def');q=dest.with_suffix('.def');assert not p.exists() and not q.exists();odb.write_def(b,str(p))
        with p.open('rb') as inp,q.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
        assert sha(p)==sha(q)
    return native,dest
source=Path('/runtime_final/pg_compact_f.odb');assert sha(source)==json.loads((C/'reports/pg_f_geometry_binding.json').read_text())['output_sha256']
contacts=json.loads((C/'reports/pg_f_contacts.json').read_text());assert contacts['source_ODB_sha256']==sha(source) and len(contacts['positive_area_PG_contacts'])==2
db,b=load(source);before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
base=json.loads((C/'reports/pg_via_plan_b.json').read_text())['planned_replacements'];sites={(905630,2216600):(905630,2218220),(1610040,566600):(1610040,568220)}
removed=Counter();added=Counter();restored=[]
for oldxy,priorxy in sites.items():
    row=next(r for r in base if r['net']=='VPWR' and tuple(r['old_xy'])==oldxy)
    assert row['stress_current_A']<.00249,'Original controlled-load current exceeds the single-cut limit'
    net=b.findNet('VPWR');found=[(sw,q) for sw in net.getSWires() for q in sw.getWires() if q.isVia() and tuple(q.getViaXY())==priorxy];assert len(found)==1;sw,old=found[0]
    assert old.getBlockVia().getName()=='W25_PG_VIA4_2_4_190_190_310_310';removed[signature('VPWR',old)]+=1
    original=b.findVia(row['old_via']);assert original and sum(q.getTechLayer().getName()=='via4' for q in original.getBoxes())==1
    new=odb.dbSBox.create(sw,original,*oldxy,str(old.getWireShapeType()));assert new;added[signature('VPWR',new)]+=1;odb.dbSBox.destroy(old)
    restored.append({'net':'VPWR','prior_xy':priorxy,'new_xy':oldxy,'new_via':row['old_via'],'cuts':1,'original_controlled_stress_current_A':row['stress_current_A']})
stack_removed,stack_added,stack=compact_stack(b);removed+=stack_removed;added+=stack_added
assert fixed(b)[:2]==before[:2] and Counter(fixed(b)[2])==Counter(before[2])-removed+added
assert wires(b)==oldw and guides(b)==oldg and obstructions(b)==oldo
native,dest=save(db,b,'pg_compact_g',True)
record={'source_sha256':sha(source),'output_sha256':sha(native),'restored_original_single_cut_vias':restored,'compacted_row_feed_stack':stack,'all_cells_graph_signal_wire_bytes_guides_obstructions_preserved':True,'planned_positions':183,'actual_via4_array_replacements':181,'via4_cuts_at_planned_positions':1430,'M4_patches':20,'accepted':False,'scope':'Two unnecessary low-current eight-cut arrays caused actual PG/PG contacts and are restored to original one-cut geometry. One local row-feed stack is compacted to three cuts per interface while retaining actual terminal metal contact. Fresh PG contact audit, full/context DRC, full-GDS core LVS and controlled IR/EM remain required.'}
(C/'reports/pg_g_geometry_binding.json').write_text(json.dumps(record,indent=2)+'\n');(C/'reports/runtime_pg_compact_g_odb.json').write_text(json.dumps({'source':str(dest),'runtime':str(native),'bytes':native.stat().st_size,'sha256':sha(native)},indent=2)+'\n')
for name in ('stream','ir'):
    state=json.loads((C/f'pg_f_{name}_state.json').read_text());state.update(odb=str(native),metrics={})
    if name=='stream':state['def']=str(native.with_suffix('.def'))
    (C/f'pg_g_{name}_state.json').write_text(json.dumps(state,indent=2)+'\n')
(C/'config_pg_g_stream.json').write_text((C/'config_pg_f_stream.json').read_text())
signal=Path('/runtime_final/li1_bridge_a.odb');proof=json.loads((C/'reports/li1_bridge_a/result.json').read_text());assert sha(signal)==proof['output_sha256'] and proof['remaining_local_markers']==1
sd,sb=load(signal);identity=fixed(sb);wire=wires(sb);guide=guides(sb);obs=obstructions(sb);subtracted,inserted,signal_stack=compact_stack(sb)
assert fixed(sb)[:2]==identity[:2] and Counter(fixed(sb)[2])==Counter(identity[2])-subtracted+inserted
assert wires(sb)==wire and guides(sb)==guide and obstructions(sb)==obs
native_signal,permanent_signal=save(sd,sb,'signal_pg_gap',False)
(C/'reports/signal_pg_gap_input.json').write_text(json.dumps({'source_sha256':sha(signal),'output_sha256':sha(native_signal),'all_cells_graph_signal_wire_bytes_guides_obstructions_preserved':True,'only_PG_change':signal_stack,'accepted':False,'scope':'The actual remaining signal/PG intersection is removed by compacting one power row-feed stack. All signal copper, including the explicit LI1 bridge and local M1 patch, remains byte-identical; full/context native DRC and all-net connectivity must confirm closure.'},indent=2)+'\n')
print('PG_G_AND_SIGNAL_GAP_INPUTS_READY',sha(native),sha(native_signal),flush=True)
