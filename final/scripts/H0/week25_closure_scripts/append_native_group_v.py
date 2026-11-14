"""Reconnect actual passive diodes with bounded, independently checked local additions."""
from pathlib import Path
from collections import Counter,defaultdict
from openroad import Tech,Design
import ast,bisect,collections,functools,heapq,hashlib,json,math,re,shutil,sys,time,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,encode_fixed
C=Path('/work/week25_closure');R=C.parent/'routing'
for file,proof in [('/runtime_final/native_group_p.odb','native_group_p/result.json'),('/runtime_final/focus_pg.odb','focus_pg_rebase.json')]:
    with Path(file).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==json.loads((C/'reports'/proof).read_text())['output_sha256']
t=Tech();design=Design(t);design.readDb('/runtime_final/native_group_p.odb')
db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
rd,rb=load('/runtime_final/focus_pg.odb')
access=json.loads((C/'reports/antenna_access.json').read_text())
targets=json.loads((C/'reports/antenna_stub_full_targets.json').read_text())['diodes']
mproof=json.loads((C/'reports/native_group_m/result.json').read_text());failed_before=set(json.loads((C/'reports/native_group_l/incomplete.json').read_text())['failed_diodes']);bad_nets={'_16390_','net3327','net4749','net660','net7318'}
old_branches={r['diode']:r for r in mproof['accepted'] if r['diode'] in failed_before and r['net'] in bad_nets};assert len(old_branches)==5
targets=[r for r in targets if r['diode'] in old_branches];assert len(targets)==5
text=(R/'scripts/search_manual_eco.py').read_text();tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='normalize_routes'];assert len(nodes)==1;exec(compile(ast.Module(body=nodes,type_ignores=[]),'normalizer','exec'))

assert json.loads((C/'reports/antenna_inserted_independent.json').read_text())['unresolved_count']==0
before=fixed(b);oldg=guides(b);oldo=obstructions(b)
original_wires=wires(b);base_geometry={}
for row in targets:
    n=b.findNet(row['net']);g=primitives(n.getWire())[0];removed=Counter(map(tuple,old_branches[row['diode']]['added_primitives']));assert not removed-g
    base=g-removed;encode_fixed(n.getWire(),base,tech,b);normalize_routes(n.getWire());assert primitives(n.getWire())[0]==base;base_geometry[row['net']]=base

out=C/'reports/native_group_v';out.mkdir(exist_ok=False)
regions=[]
for row in targets:
    xy=[p[:2] for p in row['access_points']]+[p[2:4] for p in row['closest_preserved_segments'] if p[0]<=max(20000,row['closest_preserved_segments'][0][0]+10000)]
    regions.append([min(p[0] for p in xy)-25000,min(p[1] for p in xy)-25000,max(p[0] for p in xy)+25000,max(p[1] for p in xy)+25000])
rect=lambda q:[q.xMin(),q.yMin(),q.xMax(),q.yMax()]
intersects=lambda a,z:a[0]<=z[2] and a[2]>=z[0] and a[1]<=z[3] and a[3]>=z[1]
allshapes=[]
def add(layer,q,name):
    if any(intersects(q,roi) for roi in regions):allshapes.append([layer,*q,name])
def add_primitive(q,name):
    if q[0]=='S':
        _,l,x1,y1,x2,y2,e1,e2=q;h=tech.findLayer(l).getWidth()//2
        add(l,[x1-h,y1-e1,x2+h,y2+e2] if x1==x2 else [x1-e1,y1-h,x2+e2,y2+h],name)
    elif q[0]=='R':add(q[1],list(q[2:6]),name)
    elif q[0] in ('T','V'):
        _,vn,x,y=q;v=tech.findVia(vn) if q[0]=='T' else b.findVia(vn)
        for z in v.getBoxes():add(z.getTechLayer().getName(),[z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y],name)
    else:raise AssertionError(q)
for net in b.getNets():
    if net.getWire():
        assert net.getNonDefaultRule() is None
        for q in primitives(net.getWire())[0].elements():add_primitive(q,net.getName())
    for sw in net.getSWires():
        for q in sw.getWires():
            if not q.isVia():add(q.getTechLayer().getName(),rect(q),net.getName())
            else:
                v=q.getTechVia() or q.getBlockVia();x,y=q.getViaXY()
                for z in v.getBoxes():add(z.getTechLayer().getName(),[z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y],net.getName())
relocating={'ANTENNA_7559','ANTENNA_7560','ANTENNA_7567','ANTENNA_7572'}
for i in b.getInsts():
    if i.getName() in relocating:continue
    if not any(intersects(rect(i.getBBox()),roi) for roi in regions):continue
    for p in i.getITerms():
        for layer,q in p.getGeometries():add(layer.getName(),rect(q),p.getNet().getName() if p.getNet() else '@pin')
    orient=str(i.getOrient());ox,oy=i.getLocation();mw=i.getMaster().getWidth();mh=i.getMaster().getHeight()
    assert orient in ('R0','MX','MY','R180')
    for q in i.getMaster().getObstructions():
        x1,y1,x2,y2=rect(q)
        if orient in ('MY','R180'):x1,x2=mw-x2,mw-x1
        if orient in ('MX','R180'):y1,y2=mh-y2,mh-y1
        add(q.getTechLayer().getName(),[ox+x1,oy+y1,ox+x2,oy+y2],'@obs')
for q in b.getObstructions():add(q.getBBox().getTechLayer().getName(),rect(q.getBBox()),'@block_obs')
vs=[{'name':v.getName(),'lo':v.getBottomLayer().getName(),'hi':v.getTopLayer().getName(),'boxes':[[q.getTechLayer().getName(),*rect(q)] for q in v.getBoxes()]} for v in tech.getVias() if v.getBottomLayer().getName() in ('li1','met1')]
spacing={'met1':140,'met2':140,'met3':300,'met4':300,'met5':1600,'via':170,'via2':200,'via3':200,'via4':800,'li1':170,'mcon':190}
width={l:tech.findLayer(l).getWidth() for l in ('li1','met1','met2','met3','met4','met5')}
layername=lambda n:'li1' if n==0 else 'met'+str(n)
layernum=lambda n:0 if n=='li1' else int(n[-1])
bucket=collections.defaultdict(list);data={'vias':vs};shapes=[]
code=(C/'controls/li1_bridge_a_impl.py').read_text();tree=ast.parse(code)
names={'rebuild','clear','wireok','viaok','search'}
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
source='\n'.join(ast.get_source_segment(code,n) for n in nodes)
# Include the existing cache decorators, keeping the calibrated clearance implementation unchanged.
source=source.replace('def clear(', '@functools.lru_cache(350000)\ndef clear(').replace('def wireok(', '@functools.lru_cache(350000)\ndef wireok(').replace('def viaok(', '@functools.lru_cache(200000)\ndef viaok(')
assert source.count('time.monotonic()-began>180')==1
assert source.count('if n==net:continue')==1
source=source.replace('if n==net:continue','if n==net and l in width:continue')
needle='    xs=sorted(x for x in xs if loX<=x<=hiX);ys=sorted(y for y in ys if loY<=y<=hiY)'
assert source.count(needle)==1
source=source.replace(needle,'    xs.update(x for n,x,y in native_vias if n==net and loX<=x<=hiX and loY<=y<=hiY)\n    ys.update(y for n,x,y in native_vias if n==net and loX<=x<=hiX and loY<=y<=hiY)\n'+needle)
exec(compile(source.replace('time.monotonic()-began>180','time.monotonic()-began>35'),'bounded_existing_local_planner','exec'))
native_vias=defaultdict(list)
via_boxes=lambda v:tuple(sorted((q.getTechLayer().getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax()) for q in v.getBoxes()))
for name in access['cleared_signal_nets']:
    for q in primitives(b.findNet(name).getWire())[0]:
        if q[0] in ('T','V'):
            v=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);native_vias[name,q[2],q[3]].append(via_boxes(v))
candidate_via_boxes=[tuple(sorted(tuple(q) for q in v['boxes'])) for v in vs]
@functools.lru_cache(200000)
def viaok(net,vi,x,y):
    if candidate_via_boxes[vi] in native_vias.get((net,x,y),[]):return True
    if any(l=='li1' and not inside_diode_pin([x+a,y+bb,x+c,y+d]) for l,a,bb,c,d in data['vias'][vi]['boxes']):return False
    return all(clear(net,l,x+a,y+bb,x+c,y+d) for l,a,bb,c,d in data['vias'][vi]['boxes'])

allowed_pin_rects=[]
def inside_diode_pin(q):
    return any(a<=q[0]<=q[2]<=z and c<=q[1]<=q[3]<=f for a,c,z,f in allowed_pin_rects)
@functools.lru_cache(350000)
def wireok(net,l,x1,y1,x2,y2):
    h=width[l]//2;q=[min(x1,x2)-h,min(y1,y2)-h,max(x1,x2)+h,max(y1,y2)+h]
    if l=='li1' and not inside_diode_pin(q):return False
    return clear(net,l,*q)

from pin_access_search import make_pin_access_search
search=make_pin_access_search(globals())
design.evalTclString('set_thread_count 2')
def check(tag,roi):
    design.getTritonRoute().clearDesign();p=out/(tag+'.rpt')
    design.evalTclString('drt::check_drc -box {'+' '.join(map(str,roi))+'} -output_file '+str(p)+' -marker_name DiodeStubTrial')
    text=p.read_text();markers=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text)
    assert len(markers)==text.count('violation type:');return Counter(markers)
def compact(path):
    result=[]
    for edge in path:
        if result and not edge['via'] and not result[-1]['via']:
            prev=result[-1];a,z=prev['from'],prev['to'];end=edge['to']
            if z==edge['from'] and a[2]==z[2]==end[2] and (a[0]==z[0]==end[0] or a[1]==z[1]==end[1]):prev['to']=end;continue
        result.append(dict(edge))
    return result
def append(net,path):
    existing=defaultdict(list)
    boxes=lambda v:Counter((q.getTechLayer().getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax()) for q in v.getBoxes())
    for q in primitives(net.getWire())[0]:
        if q[0] in ('T','V'):
            via=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1])
            existing[q[2],q[3]].append(boxes(via))
    e=odb.dbWireEncoder();e.append(net.getWire());added=Counter()
    for edge in path:
        a,z=edge['from'],edge['to']
        if edge['via']:
            v=tech.findVia(edge['via']);assert v
            if boxes(v) in existing[tuple(a[:2])]:
                print('EXACT_EXISTING_VIA_REUSED',net.getName(),v.getName(),a[:2],flush=True);continue
            e.newPath(v.getBottomLayer(),'ROUTED');e.addPoint(*a[:2]);e.addTechVia(v)
            added[('T',v.getName(),*a[:2])]+=1
        else:
            l=layername(a[2]);assert a[2]==z[2] and ((a[0]==z[0]) != (a[1]==z[1]))
            e.newPath(tech.findLayer(l),'ROUTED');e.addPoint(*a[:2]);e.addPoint(*z[:2])
            ax,zx=sorted((a[:2],z[:2]));h=width[l]//2;added[('S',l,*ax,*zx,h,h)]+=1
    e.end();return added
def append_patches(net,patches):
    e=odb.dbWireEncoder();e.append(net.getWire());result=Counter()
    for q in patches:
        _,layer,x1,y1,x2,y2=q
        assert x1<x2 and y1<y2 and layer in width
        e.newPath(tech.findLayer(layer),'ROUTED');e.addPoint(x1,y1);e.addRect(0,0,x2-x1,y2-y1);result[q]+=1
    e.end();return result
def repair_gaps(net,baseline,after,roi,tag):
    additions=Counter()
    for iteration in range(6):
        new=after-baseline
        if not new:break
        if any(kind not in ('Metal Spacing','NS Metal','Min Hole') or set(re.findall(r'net:([^\s]+)',src))!={net.getName()} for kind,src,box in new):break
        patches=[]
        for kind,src,box in new:
            m=re.fullmatch(r'\(([-0-9.]+), ([-0-9.]+)\) - \(([-0-9.]+), ([-0-9.]+)\) on Layer (\w+)',box);assert m,box
            x1,y1,x2,y2=[round(float(v)*1000) for v in m.groups()[:4]];layer=m[5]
            if layer not in width:return additions,after
            q=('R',layer,x1-5,y1-5,x2+5,y2+5)
            if layer=='li1' and not inside_diode_pin(q[2:6]):return additions,after
            assert roi[0]<=q[2]<q[4]<=roi[2] and roi[1]<=q[3]<q[5]<=roi[3]
            patches.append(q)
        additions+=append_patches(net,patches)
        updated=check(tag+f'_patch{iteration}',roi)
        if updated==after:after=updated;break
        after=updated
    return additions,after

def cell_geometry(inst):
    result=[]
    for pin in inst.getITerms():
        for layer,q in pin.getGeometries():result.append([layer.getName(),*rect(q),pin.getNet().getName() if pin.getNet() else '@pin'])
    orient=str(inst.getOrient());ox,oy=inst.getLocation();mw=inst.getMaster().getWidth();mh=inst.getMaster().getHeight()
    assert orient in ('R0','MX','MY','R180')
    for q in inst.getMaster().getObstructions():
        x1,y1,x2,y2=rect(q)
        if orient in ('MY','R180'):x1,x2=mw-x2,mw-x1
        if orient in ('MX','R180'):y1,y2=mh-y2,mh-y1
        result.append([q.getTechLayer().getName(),ox+x1,oy+y1,ox+x2,oy+y2,'@obs'])
    return result

accepted=[];paths=defaultdict(list);failed=[];relocations=[]
prior=json.loads((C/'reports/native_group_r/incomplete.json').read_text())['accepted'];assert len(prior)==1
for row in prior:
    n=b.findNet(row['net']);added=append(n,row['path']);patches=[tuple(q) for q in row['added_primitives'] if q[0]=='R']
    if patches:added+=append_patches(n,patches)
    assert added==Counter(map(tuple,row['added_primitives']))
    accepted.append({**row,'replayed_checked_inside_pin_branch':'native_group_r'});paths[row['net']].append(row['path'])
    for q in added.elements():add_primitive(q,row['net'])
print('REPLAYED_R_INSIDE_PIN_BRANCH',flush=True)
for row,roi in zip(targets,regions):
    if row['diode'] not in relocating:continue
    diode=b.findInst(row['diode']);name=row['net'];net=b.findNet(name);original=primitives(net.getWire())[0]
    old=tuple(diode.getLocation());orient=str(diode.getOrient());w=diode.getMaster().getWidth();h=diode.getMaster().getHeight();own=list(diode.findITerm('DIODE').getPrefAccessPoints());assert own
    px,py=own[0].getPoint();goal=tuple(old_branches[row['diode']]['path'][-1]['to']);assert goal[2] in (1,2)
    boxes=[rect(i.getBBox()) for i in b.getInsts() if i.getName()!=diode.getName()]
    occupied=defaultdict(list)
    for a,c,z,f in boxes:
        if a>roi[2] or z<roi[0] or c>roi[3] or f<roi[1]:continue
        for y in range(c//2720,f//2720+1):occupied[y].append((a,c,z,f))
    candidates=[]
    for rr in b.getRows():
        q=rect(rr.getBBox());y=q[1]
        if str(rr.getOrient())!=orient or abs(y+py-goal[1])>15000 or (y-old[1])%340:continue
        x0=q[0]+round((goal[0]-px-q[0])/460)*460
        near={tuple(v) for yy in range(y//2720,(y+h)//2720+1) for v in occupied[yy]}
        for offset in range(-32,33):
            x=x0+offset*460
            if x<max(q[0],roi[0]+2000) or x+w>min(q[2],roi[2]-2000) or y<roi[1]+2000 or y+h>roi[3]-2000 or (x-old[0])%460:continue
            if any(x<a2 and x+w>a1 and y<b2 and y+h>b1 for a1,b1,a2,b2 in near):continue
            distance=abs(x+px-goal[0])+abs(y+py-goal[1]);candidates.append((distance,x,y))
    candidates=sorted(set(candidates));print('FREE_SAME_PHASE_PLACEMENTS',row['diode'],len(candidates),'cells',len(boxes),flush=True)
    found=False;attempts=[]
    for index,(distance,x,y) in enumerate(candidates[:80]):
        diode.setLocation(x,y)
        allowed_pin_rects[:]=[rect(q) for l,q in diode.findITerm('DIODE').getGeometries() if l.getName()=='li1'];assert allowed_pin_rects
        data['region']=roi;shapes=[q for q in allshapes if intersects(q[1:5],roi)]
        shapes.extend(cell_geometry(diode))
        rebuild();start=(x+px,y+py,0);path=search(name,start,goal)
        if path is None:attempts.append({'location':[x,y],'legal_path':False});continue
        path=compact(path);added=append(net,path);assert primitives(net.getWire())[0]==original+added
        after=check(row['diode']+f'_placement{index}',roi)
        if not after:
            paths[name].append(path);accepted.append({'diode':row['diode'],'net':name,'path':path,'added_primitives':list(added.elements()),'local_native_new_markers':0,'placement_trial':index})
            relocations.append({'diode':row['diode'],'master':diode.getMaster().getName(),'net':name,'old_location':list(old),'new_location':[x,y],'orientation':orient,'same_phase_and_empty_native_row_slot':True,'local_native_DRC':0,'attempts':attempts})
            for q in added.elements():add_primitive(q,name)
            for shape in cell_geometry(diode):add(shape[0],shape[1:5],shape[-1])
            found=True;print('RELOCATED_AND_CONNECTED',row['diode'],old,(x,y),len(path),flush=True);break
        attempts.append({'location':[x,y],'local_native_markers':sum(after.values())})
        encode_fixed(net.getWire(),original,tech,b);normalize_routes(net.getWire());assert primitives(net.getWire())[0]==original
    if not found:
        diode.setLocation(*old);failed.append(row['diode']);print('NO_ACCEPTED_RELOCATION',row['diode'],flush=True)
    (out/'progress.json').write_text(json.dumps({'accepted':accepted,'relocations':relocations,'failed_diodes':failed,'accepted_for_final':False},indent=2)+'\n')
if failed:
    (out/'incomplete.json').write_text(json.dumps({'accepted':accepted,'failed_diodes':failed,'accepted_for_final':False},indent=2)+'\n')
    raise AssertionError(('Some diodes lack a checked inside-pin M1-access branch',failed))
assert len(accepted)==5 and len(relocations)==4 and guides(b)==oldg and obstructions(b)==oldo
expected=dict(before[0])
for row in relocations:
    old=expected[row['diode']];assert list(old[2])==row['old_location'];expected[row['diode']]=(old[0],old[1],tuple(row['new_location']),old[3])
assert fixed(b)==(expected,before[1],before[2]),'Only the four reviewed added passive diode locations may change'
response=str(design.evalTclString('set e [catch {check_placement -verbose} msg]; list $e $msg'));assert response.startswith('0 '),response

changed=set(paths);assert {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in original_wires.items() if n not in changed}
for name in changed:
    additions=Counter(q for row in accepted if row['net']==name for q in map(tuple,row['added_primitives']))
    assert primitives(b.findNet(name).getWire())[0]==base_geometry[name]+additions
antenna=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final/native_group_v.odb');target=C/'inputs/native_group_v.odb';assert not native.exists() and not target.exists()
odb.write_db(db,str(native))
with native.open('rb') as inp,target.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(native)==sha(target)
(out/'result.json').write_text(json.dumps({'accepted_for_final':False,'output_sha256':sha(native),'antenna_nets':antenna,'rerouted_diode_branches':len(accepted),'passive_diodes_added':20,'accepted':accepted,'all_P_source_copper_except_five_replaced_branches_preserved':True,'pin_access_method':'5nm mcon centre enumeration inside the unchanged diode pin; M1/M2 search only','new_LI1_restricted_to_actual_diode_LEF_pin':True,'all_original_cells_graph_PG_guides_obstructions_unchanged':True,'only_added_passive_diode_locations_changed':relocations,'placement_response':response,'scope':'Only explicit local diode branches added; full native/context DRC, all-net connectivity, full-GDS core LVS and fresh electrical checks still required.'},indent=2)+'\n')
print('DIODE_STUB_CANDIDATE_READY',sha(native),'antenna',antenna,flush=True)
