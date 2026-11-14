"""Replace high-current single-cut PG vias with real eight-cut arrays on existing M4."""
from pathlib import Path
from collections import Counter
import hashlib,json,math,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions
C=Path('/work/week25_closure');source=Path('/runtime/F.odb')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='fe627dd4b1ff4c152dcfa9dd5d08b05c13b7272ab4065d7f0cb8af3d87dd1380'
db,b=load(source);u=b.getDbUnitsPerMicron();assert u==1000
before=fixed(b);old_wires=wires(b);old_guides=guides(b);old_obs=obstructions(b)
currents=json.loads((C/'controls/pg_via_currents.json').read_text());threshold=currents['selection_threshold_A']
support={n:{'met4':[],'met5':[]} for n in ('VPWR','VGND')};physical={};swires={}
def rect(q):return (q.xMin(),q.yMin(),q.xMax(),q.yMax())
def contains(a,z):return a[0]<=z[0] and a[1]<=z[1] and a[2]>=z[2] and a[3]>=z[3]
def distance(a,z):return math.hypot(max(a[0]-z[2],z[0]-a[2],0),max(a[1]-z[3],z[1]-a[3],0))
for name in support:
    net=b.findNet(name)
    for sw in net.getSWires():
        for q in sw.getWires():
            if not q.isVia():
                layer=q.getTechLayer().getName()
                if layer in support[name]:support[name][layer].append(rect(q))
                continue
            via=q.getBlockVia() or q.getTechVia()
            if any(z.getTechLayer().getName()=='via4' for z in via.getBoxes()):
                x,y=q.getViaXY();key=(name,x,y);assert key not in physical,key
                physical[key]=q;swires[key]=sw
    for i in b.getInsts():
        if not i.getMaster().isBlock():continue
        for p in i.getITerms():
            if p.getNet() is None or p.getNet().getName()!=name:continue
            for layer,z in p.getGeometries():
                if layer.getName() in support[name]:support[name][layer.getName()].append(rect(z))
planned=[];skipped=[];mapping=[]
for name in ('VPWR','VGND'):
    opposite='VGND' if name=='VPWR' else 'VPWR'
    matched={}
    for edge in currents['cases']['0p028'][name]['edges']:
        current=edge['current_A']
        if current<=threshold:continue
        matches={(name,*xy) for xy in (edge['lower_xy'],edge['upper_xy']) if (name,*xy) in physical}
        if len(matches)!=1:
            row={'net':name,**edge,'physical_candidates':[list(v) for v in matches]}
            mapping.append(row)
            continue
        key=next(iter(matches));assert key not in matched,('Multiple electrical branches per via',key)
        matched[key]=current
    for key,current in sorted(matched.items()):
        _,x,y=key
        box=physical[key];old=box.getBlockVia();assert old is not None and old.hasParams()
        cuts=[q for q in old.getBoxes() if q.getTechLayer().getName()=='via4'];count=len(cuts)
        if current/count<=threshold:continue
        original=old.getViaParams();assert original.getXCutSize()==original.getYCutSize()==800
        assert original.getXCutSpacing()==original.getYCutSpacing()==800
        assert all(getattr(original,'get'+v)()==0 for v in ('XOrigin','YOrigin','XBottomOffset','YBottomOffset','XTopOffset','YTopOffset'))
        top=next(rect(q) for q in old.getBoxes() if q.getTechLayer().getName()=='met5')
        old_top=(x+top[0],y+top[1],x+top[2],y+top[3]);assert any(contains(z,old_top) for z in support[name]['met5'])
        choice=None
        for cols,rows in ((2,4),(1,8),(4,2),(8,1)):
            cw,ch=800*cols+800*(cols-1),800*rows+800*(rows-1)
            bx,by=190,190;tx,ty=max(310,(1600-cw)//2),max(310,(1600-ch)//2)
            bw,bh,tw,th=cw+2*bx,ch+2*by,cw+2*tx,ch+2*ty
            centers=[(x,y),(x,old_top[3]-th//2),(x,old_top[1]+th//2),(old_top[2]-tw//2,y),(old_top[0]+tw//2,y)]
            for nx,ny in centers:
                bottom=(nx-bw//2,ny-bh//2,nx+bw//2,ny+bh//2)
                upper=(nx-tw//2,ny-th//2,nx+tw//2,ny+th//2)
                if not any(contains(z,bottom) for z in support[name]['met4']):continue
                if any(distance(z,upper)<1600 for z in support[opposite]['met5']):continue
                choice={'cols':cols,'rows':rows,'XBottomEnclosure':bx,'YBottomEnclosure':by,'XTopEnclosure':tx,'YTopEnclosure':ty,'new_xy':[nx,ny],'new_bottom_box':bottom,'new_top_box':upper};break
            if choice:break
        if choice is None:
            skipped.append({'net':name,'old_xy':[x,y],'current_A':current,'reason':'No eight-cut shape wholly inside existing same-net M4 support and clear of opposite M5 by 1.6um'})
            continue
        planned.append({'net':name,'old_xy':[x,y],'old_via':old.getName(),'old_cut_count':count,'old_bbox':rect(box),'stress_current_A':current,**choice})
        support[name]['met5'].append(tuple(choice['new_top_box']))
required_unfixed=[r for r in skipped if r['current_A']>.00249]+[r for r in mapping if r['current_A']>.00249]
plan={'accepted':False,'source_sha256':sha(source),'intended_limit_mA_per_cut':2.49,'limit_temperature_C':90,'planned_replacements':planned,'skipped':skipped,'unmapped_or_ambiguous_edges':mapping,'unfixed_required':required_unfixed,'scope':'PG-only controlled-load trial on frozen filler baseline. Existing source M4 support contains every new bottom rectangle; opposite-net M5 clearance screened. Unmapped branches below the entire-current-on-one-cut limit remain explicitly listed. Signal-wire collisions, full GDS DRC, fresh IR/EM and final 50-driver implementation still require verification.'}
(C/'reports/pg_via_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
assert not required_unfixed,f'{len(required_unfixed)} required sites remain unsupported; see reports/pg_via_plan.json'
assert len(planned)>90
props=('BottomLayer','CutLayer','TopLayer','NumCutCols','NumCutRows','XCutSize','YCutSize','XCutSpacing','YCutSpacing','XOrigin','YOrigin','XBottomEnclosure','YBottomEnclosure','XTopEnclosure','YTopEnclosure','XBottomOffset','YBottomOffset','XTopOffset','YTopOffset')
masters={};removed=[];added=[]
for r in planned:
    name=r['net'];x,y=r['old_xy'];box=physical[name,x,y];old=box.getBlockVia();p=old.getViaParams()
    signature=(r['cols'],r['rows'],r['XBottomEnclosure'],r['YBottomEnclosure'],r['XTopEnclosure'],r['YTopEnclosure'])
    if signature not in masters:
        vname='W25_PG_VIA4_'+'_'.join(map(str,signature));v=odb.dbVia.create(b,vname);assert v is not None
        params=odb.dbViaParams()
        for prop in props:getattr(params,'set'+prop)(getattr(p,'get'+prop)())
        params.setNumCutCols(r['cols']);params.setNumCutRows(r['rows'])
        for prop in ('XBottomEnclosure','YBottomEnclosure','XTopEnclosure','YTopEnclosure'):getattr(params,'set'+prop)(r[prop])
        v.setViaGenerateRule(old.getViaGenerateRule());v.setViaParams(params)
        assert sum(q.getTechLayer().getName()=='via4' for q in v.getBoxes())==8
        masters[signature]=v
    assert sum(q.getTechLayer().getName()=='via4' for q in old.getBoxes())==r['old_cut_count']
    removed.append((name,*rect(box),old.getName()))
    nx,ny=r['new_xy'];new=odb.dbSBox.create(swires[name,x,y],masters[signature],nx,ny,str(box.getWireShapeType()));assert new is not None
    added.append((name,*rect(new),masters[signature].getName()));r['new_via']=masters[signature].getName();r['new_bbox']=rect(new)
    odb.dbSBox.destroy(box)
after=fixed(b)
assert after[:2]==before[:2] and wires(b)==old_wires and guides(b)==old_guides and obstructions(b)==old_obs
assert Counter(before[2])-Counter(after[2])==Counter(removed) and Counter(after[2])-Counter(before[2])==Counter(added)
target=C/'inputs/pg_via_trial.odb';assert not target.exists();odb.write_db(db,str(target))
plan.update(output_sha256=sha(target),only_planned_PG_via_shapes_changed=True,all_cells_signal_graph_routes_guides_obstructions_unchanged=True,total_new_cuts=8*len(planned),new_via_definitions=len(masters))
(C/'reports/pg_via_plan.json').write_text(json.dumps(plan,indent=2)+'\n')
state=json.loads((C.parent/'week25_signoff/ir_state.json').read_text());state.update(odb=str(target),metrics={})
for key in ('gds','klayout_gds','def'):state.pop(key,None)
(C/'pg_ir_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C.parent/'week25_signoff/config_ir.json').read_text());(C/'config_pg_ir.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('PG_VIA_TRIAL_READY',len(planned),'replacements',8*len(planned),'cuts',len(skipped),'unneeded unsupported candidates',flush=True)
