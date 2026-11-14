"""Reconnect actual passive diodes with bounded, independently checked local additions."""
from pathlib import Path
from collections import Counter,defaultdict
from openroad import Tech,Design
import ast,bisect,collections,functools,heapq,hashlib,json,math,re,shutil,sys,time,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');R=C.parent/'routing'
t=Tech();design=Design(t);design.readDb('/runtime_final/antenna_ready.odb')
db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
rd,rb=load('/runtime_final/focus_pg.odb')
access=json.loads((C/'reports/antenna_access.json').read_text())
targets=json.loads((C/'reports/antenna_stub_targets.json').read_text())['diodes']
assert json.loads((C/'reports/antenna_inserted_independent.json').read_text())['unresolved_count']==0
before=fixed(b);oldg=guides(b);oldo=obstructions(b)
for name in access['cleared_signal_nets']:
    n=b.findNet(name);assert not n.getWire()
    w=odb.dbWire.create(n);w.append(rb.findNet(name).getWire())
assert wires(b)==wires(rb),'Restoring preserved routes changed original wire bytes'
original_wires=wires(b)
out=C/'reports/antenna_stubs_a';out.mkdir(exist_ok=False)
regions=[]
for row in targets:
    xy=[p[:2] for p in row['access_points']]+[p[2:4] for p in row['closest_preserved_segments'][:8]]
    regions.append([min(p[0] for p in xy)-6000,min(p[1] for p in xy)-6000,max(p[0] for p in xy)+6000,max(p[1] for p in xy)+6000])
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
for i in b.getInsts():
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
vs=[{'name':v.getName(),'lo':v.getBottomLayer().getName(),'hi':v.getTopLayer().getName(),'boxes':[[q.getTechLayer().getName(),*rect(q)] for q in v.getBoxes()]} for v in tech.getVias() if v.getBottomLayer().getName() in ('li1','met1','met2','met3','met4')]
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
exec(compile(source.replace('time.monotonic()-began>180','time.monotonic()-began>35'),'bounded_existing_local_planner','exec'))
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
    e=odb.dbWireEncoder();e.append(net.getWire());added=Counter()
    for edge in path:
        a,z=edge['from'],edge['to']
        if edge['via']:
            v=tech.findVia(edge['via']);assert v
            e.newPath(v.getBottomLayer(),'ROUTED');e.addPoint(*a[:2]);e.addTechVia(v)
            added[('T',v.getName(),*a[:2])]+=1
        else:
            l=layername(a[2]);assert a[2]==z[2] and ((a[0]==z[0]) != (a[1]==z[1]))
            e.newPath(tech.findLayer(l),'ROUTED');e.addPoint(*a[:2]);e.addPoint(*z[:2])
            ax,zx=sorted((a[:2],z[:2]));h=width[l]//2;added[('S',l,*ax,*zx,h,h)]+=1
    e.end();return added
accepted=[];paths=defaultdict(list)
for row,roi in zip(targets,regions):
    name=row['net'];net=b.findNet(name);original=primitives(net.getWire())[0]
    data['region']=roi;shapes=[q for q in allshapes if intersects(q[1:5],roi)];rebuild()
    current=check(row['diode']+'_before',roi);found=False;goals=[]
    for _,layer,x,y,*_ in row['closest_preserved_segments']:
        point=(x,y,layernum(layer))
        if point not in goals:goals.append(point)
    for trial,end in enumerate(goals[:6]):
        ax,ay,al=row['access_points'][0];start=(ax,ay,layernum(al))
        path=search(name,start,end)
        if path is None:continue
        path=compact(path);added=append(net,path)
        assert primitives(net.getWire())[0]==original+added
        after=check(row['diode']+f'_trial{trial}',roi)
        if not after-current:
            paths[name].append(path);accepted.append({'diode':row['diode'],'net':name,'path':path,'added_primitives':list(added.elements()),'local_native_new_markers':0})
            for q in added.elements():add_primitive(q,name)
            found=True;print('DIODE_STUB_ACCEPTED',row['diode'],name,len(path),flush=True);break
        odb.dbWire.destroy(net.getWire());netwire=odb.dbWire.create(net);netwire.append(rb.findNet(name).getWire())
        for prior in paths[name]:append(net,prior)
        assert primitives(net.getWire())[0]==original
    if not found:
        (out/'incomplete.json').write_text(json.dumps({'accepted':accepted,'failed_diode':row['diode'],'accepted_for_final':False},indent=2)+'\n')
        raise AssertionError(('No independently clean local diode stub',row['diode']))
assert len(accepted)==20 and fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
changed=set(paths);assert {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in original_wires.items() if n not in changed}
for name in changed:
    additions=Counter(q for row in accepted if row['net']==name for q in map(tuple,row['added_primitives']))
    assert primitives(b.findNet(name).getWire())[0]==primitives(rb.findNet(name).getWire())[0]+additions
antenna=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final/antenna_stubs_a.odb');target=C/'inputs/antenna_stubs_a.odb';assert not native.exists() and not target.exists()
odb.write_db(db,str(native))
with native.open('rb') as inp,target.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(native)==sha(target)
(out/'result.json').write_text(json.dumps({'accepted_for_final':False,'output_sha256':sha(native),'antenna_nets':antenna,'diodes_connected_with_checked_stubs':len(accepted),'accepted':accepted,'all_original_signal_copper_preserved':True,'all_cells_graph_PG_guides_obstructions_unchanged':True,'scope':'Only explicit local diode branches added; full native/context DRC, all-net connectivity, full-GDS core LVS and fresh electrical checks still required.'},indent=2)+'\n')
print('DIODE_STUB_CANDIDATE_READY',sha(native),'antenna',antenna,flush=True)
