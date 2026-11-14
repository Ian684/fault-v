"""Apply the calibrated small conflict-cover repair to a complete routed checkpoint."""
from pathlib import Path
from collections import Counter,defaultdict
import hashlib,json,re,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,encode_fixed,path_type,restore_exact
C=Path('/work/week25_closure');source=C/'runs/minimal_route_a/1-openroad-detailedrouting/drt_iter13.odb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads((C/'reports/minimal13_independent_b.json').read_text());assert check['odb_sha256']==sha(source)
assert check['unresolved_count']>0
db,b=load(source);rd,rb=load(source);gd,gb=load(C/'inputs/cached_guided.odb')
before=fixed(b);old_wires=wires(b);assert len(old_wires)==41337
targets={'_39335_','_37262_'}
for name in targets:
    inst=b.findInst(name);other=gb.findInst(name);assert inst and other
    assert inst.getMaster().getName().rsplit('_',1)[0]==other.getMaster().getName().rsplit('_',1)[0]
    assert int(other.getMaster().getName().rsplit('_',1)[1])==2*int(inst.getMaster().getName().rsplit('_',1)[1])
    assert inst.swapMaster(db.findMaster(other.getMaster().getName()))
    inst.setOrient(str(other.getOrient()));inst.setLocation(*other.getLocation())
    inst.setPlacementStatus(str(other.getPlacementStatus()))
assert fixed(b)==fixed(gb) and obstructions(b)==obstructions(gb),'Physical/logical candidate differs from verified 50-driver placement'
peers=defaultdict(list)
for i in b.getInsts():
    if i.getName() not in targets:peers[i.getMaster().getName(),str(i.getOrient())].append(i)
for name in targets:
    inst=b.findInst(name);x,y=inst.getLocation();chosen=None
    for p in peers[inst.getMaster().getName(),str(inst.getOrient())]:
        px,py=p.getLocation()
        if (x-px)%460 or (y-py)%340:continue
        valid=True
        for pin in inst.getITerms():
            if str(pin.getMTerm().getSigType()) in ('POWER','GROUND'):continue
            aps=p.findITerm(pin.getMTerm().getName()).getPrefAccessPoints()
            if not aps or any(not any(l.getName()==a.getLayer().getName() and z.xMin()<=x+a.getPoint()[0]<=z.xMax() and z.yMin()<=y+a.getPoint()[1]<=z.yMax() for l,z in pin.getGeometries()) for a in aps):valid=False;break
        if valid:chosen=p;break
    assert chosen is not None,name
    inst.setPinAccessIdx(chosen.getPinAccessIdx())
    for pin in inst.getITerms():
        pin.clearPrefAccessPoints()
        for a in chosen.findITerm(pin.getMTerm().getName()).getPrefAccessPoints():pin.setAccessPoint(a.getMPin(),a)
conflicts=[]
for marker in check['unresolved']:
    names=set(re.findall(r'net:([^\s]+)',marker['srcs']))
    assert names,marker
    assert all(b.findNet(n) is not None for n in names),names
    conflicts.append(names)
def eligible(name):
    n=b.findNet(name)
    return str(n.getSigType()) in ('SIGNAL','CLOCK') and n.getWire() is not None and n.getNonDefaultRule() is None
remaining=conflicts[:];dirty=set()
while remaining:
    counts=Counter(n for names in remaining for n in names if eligible(n));assert counts,remaining
    name=min(counts,key=lambda n:(-counts[n],str(b.findNet(n).getSigType())=='CLOCK',n))
    dirty.add(name);remaining=[v for v in remaining if name not in v]
rois=[]
for name in targets:
    i=b.findInst(name);r=i.getBBox();rois.append((r.xMin()-2000,r.yMin()-2000,r.xMax()+2000,r.yMax()+2000))
    dirty.update(p.getNet().getName() for p in i.getITerms() if p.getNet() and str(p.getMTerm().getSigType()) not in ('POWER','GROUND'))
def touches(box):
    a,c,z,f=box;return any(a<=x1 and z>=x0 and c<=y1 and f>=y0 for x0,y0,x1,y1 in rois)
for net in b.getNets():
    if not eligible(net.getName()) or net.getName() in dirty:continue
    for q in primitives(net.getWire())[0]:
        if q[0]=='S' and q[1] in ('li1','met1','met2'):
            _,layer,x0,y0,x1,y1,*_=q;hit=touches((min(x0,x1)-500,min(y0,y1)-500,max(x0,x1)+500,max(y0,y1)+500))
        elif q[0] in ('T','V'):_,via,x,y=q;hit=touches((x-500,y-500,x+500,y+500))
        elif q[0]=='R' and q[1] in ('li1','met1','met2'):hit=touches(tuple(q[2:]))
        else:hit=False
        if hit:dirty.add(net.getName());break
assert 0<len(dirty)<=200 and all(dirty&v for v in conflicts)
expected=guides(b);fresh=guides(gb)
for name in dirty:
    net=b.findNet(name)
    for g in list(net.getGuides()):odb.dbGuide.destroy(g)
    for layer,via,box,congested,connected,jumper in fresh[name]:
        g=odb.dbGuide_create(net,db.getTech().findLayer(layer),db.getTech().findLayer(via),odb.Rect(*box),congested)
        g.setIsConnectedToTerm(connected);g.setIsJumper(jumper)
    expected[name]=fresh[name]
identity=fixed(b);obs=obstructions(b);assert wires(b)==old_wires and guides(b)==expected
reference=C/'inputs/focus_reference.odb';target=C/'inputs/focus_protected.odb';assert not target.exists() and not reference.exists()
odb.write_db(db,str(reference));protected=[]
for net in b.getNets():
    if not net.getWire() or net.getName() in dirty:continue
    assert path_type(net.getWire())=='ROUTED'
    geometry=primitives(net.getWire())[0];encode_fixed(net.getWire(),geometry,db.getTech(),b);net.setWireType('FIXED')
    assert primitives(net.getWire())[0]==geometry;protected.append(net.getName())
assert fixed(b)==identity and obstructions(b)==obs and guides(b)==expected
odb.write_db(db,str(target));restore_exact(b,rb,protected)
assert wires(b)==old_wires
state=json.loads((C/'cached_route_state.json').read_text());state.update(odb=str(target),metrics={})
(C/'focus_route_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_cached_route.json').read_text());cfg['DRT_THREADS']=4
(C/'config_focus_route.json').write_text(json.dumps(cfg,indent=2)+'\n')
record={'accepted':False,'source_sha256':sha(source),'reference_sha256':sha(reference),'protected_sha256':sha(target),'source_actual_unresolved_DRC':check['unresolved_count'],'editable_nets':sorted(dirty),'protected_nets':protected,'all_initial_41337_routes_retained':True,'cells_graph_PG_match_verified_50_driver_candidate':True,'all_real_conflicts_covered':True,'all_protected_primitive_geometry_unchanged':True,'all_protected_wire_bytes_roundtrip_exact':True,'scope':'Complete routed checkpoint, not a broad partial route. Calibrated ALL/NEARDRC local repair on a complete conflict cover; unrelated original routes and guides retained. Temporary FIXED status must be normalized and every final gate independently rerun.'}
(C/'reports/focus_route_input.json').write_text(json.dumps(record,indent=2)+'\n')
print('FOCUS_CLOSURE_READY',len(dirty),'editable',len(protected),'protected',flush=True)
