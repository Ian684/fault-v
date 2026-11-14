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

out=C/'reports/native_group_s';out.mkdir(exist_ok=False)
regions=[]
for row in targets:
    xy=[p[:2] for p in row['access_points']]+[p[2:4] for p in row['closest_preserved_segments'] if p[0]<=max(20000,row['closest_preserved_segments'][0][0]+10000)]
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
vs=[{'name':v.getName(),'lo':v.getBottomLayer().getName(),'hi':v.getTopLayer().getName(),'boxes':[[q.getTechLayer().getName(),*rect(q)] for q in v.getBoxes()]} for v in tech.getVias() if v.getBottomLayer().getName() in ('li1','met1','met2','met3')]
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

rows=[]
for row,roi in zip(targets,regions):
    pins=[rect(q) for l,q in b.findInst(row['diode']).findITerm('DIODE').getGeometries() if l.getName()=='li1']
    rows.append({'target':row,'roi':roi,'pins':pins,'old_branch':old_branches[row['diode']]})
(out/'access_geometry.json').write_text(json.dumps({'rows':rows,'shapes':allshapes,'vias':vs,'spacing':spacing,'width':width})+'\n')
print('PIN_ACCESS_GEOMETRY_EXPORTED',len(rows),len(allshapes),flush=True)
