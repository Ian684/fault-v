"""Reuse the project's bounded obstacle-aware planner for five confirmed crossings."""
from pathlib import Path
from collections import Counter,defaultdict
from openroad import Tech,Design
import ast,collections,functools,heapq,hashlib,json,re,sys,odb,shutil
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/runtime/focus_final.odb')
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
rd,rb=load(source);before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
metal={'li1','met1','met2','met3','met4','met5'}
for file,names in [(R/'scripts/search_manual_eco.py',{'normalize_routes','restore_patches'}),(R/'scripts/check_antenna_signal_connectivity.py',{'connectivity'}),(C/'scripts/search_short_bridges.py',{'segment','via_ids'})]:
    tree=ast.parse(file.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file.name,'exec'))
fine=len(sys.argv)>1 and sys.argv[1]=='fine'
out=C/('reports/short_paths_fine' if fine else 'reports/short_paths_b');out.mkdir(exist_ok=False);design.evalTclString('set_thread_count 2')
region=[1575000,625000,1618000,649000];shapes=[]
rect=lambda q:[q.xMin(),q.yMin(),q.xMax(),q.yMax()]
def add(layer,q,name):
    if q[0]<=region[2] and q[2]>=region[0] and q[1]<=region[3] and q[3]>=region[1]:shapes.append([layer,*q,name])
def add_wire(net):
    for q in primitives(net.getWire())[0].elements():
        if q[0]=='S':
            _,l,x1,y1,x2,y2,e1,e2=q;h=tech.findLayer(l).getWidth()//2
            add(l,[x1-h,y1-e1,x2+h,y2+e2] if x1==x2 else [x1-e1,y1-h,x2+e2,y2+h],net.getName())
        elif q[0]=='R':add(q[1],list(q[2:6]),net.getName())
        elif q[0] in ('T','V'):
            _,name,x,y=q
            if not (region[0]-3000<=x<=region[2]+3000 and region[1]-3000<=y<=region[3]+3000):continue
            v=tech.findVia(name) if q[0]=='T' else b.findVia(name)
            for z in v.getBoxes():add(z.getTechLayer().getName(),[z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y],net.getName())
        else:raise AssertionError(q)
for net in b.getNets():
    if net.getWire():assert net.getNonDefaultRule() is None;add_wire(net)
    for sw in net.getSWires():
        for q in sw.getWires():
            if not q.isVia():add(q.getTechLayer().getName(),rect(q),net.getName())
            else:
                v=q.getTechVia() or q.getBlockVia();x,y=q.getViaXY()
                for z in v.getBoxes():add(z.getTechLayer().getName(),[z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y],net.getName())
for i in b.getInsts():
    z=rect(i.getBBox())
    if z[0]>region[2] or z[2]<region[0] or z[1]>region[3] or z[3]<region[1]:continue
    for p in i.getITerms():
        for layer,q in p.getGeometries():add(layer.getName(),rect(q),p.getNet().getName() if p.getNet() else '@pin')
    orient=str(i.getOrient());ox,oy=i.getLocation();mw=i.getMaster().getWidth();mh=i.getMaster().getHeight();assert orient in ('R0','MX','MY','R180')
    for q in i.getMaster().getObstructions():
        x1,y1,x2,y2=rect(q)
        if orient in ('MY','R180'):x1,x2=mw-x2,mw-x1
        if orient in ('MX','R180'):y1,y2=mh-y2,mh-y1
        add(q.getTechLayer().getName(),[ox+x1,oy+y1,ox+x2,oy+y2],'@obs')
for q in b.getObstructions():add(q.getBBox().getTechLayer().getName(),rect(q.getBBox()),'@block_obs')
vs=[]
for v in tech.getVias():
    if v.getBottomLayer().getName() in ('met1','met2','met3'):
        vs.append({'name':v.getName(),'lo':v.getBottomLayer().getName(),'hi':v.getTopLayer().getName(),'boxes':[[q.getTechLayer().getName(),*rect(q)] for q in v.getBoxes()]})
data={'region':region,'shapes':shapes,'vias':vs};(out/'obstacles.json').write_text(json.dumps(data)+'\n')
spacing={'met1':140,'met2':140,'met3':300,'met4':300,'via':170,'via2':200,'via3':200};width={'met1':140,'met2':140,'met3':300,'met4':300}
planner_text=(R/'scripts/plan_manual_free.py').read_text()
if fine:
    steps='[(230,0),(-230,0),(0,170),(0,-170)]';assert planner_text.count(steps)==1
    planner_text=planner_text.replace(steps,'[(5,0),(-5,0),(0,5),(0,-5)]').replace('count+=1','count+=1\n  if count>250000:\n   print("BOUNDED_SEARCH_LIMIT",net,flush=True);return None').replace('@functools.lru_cache(None)','@functools.lru_cache(200000)')
planner=ast.parse(planner_text);functions=[n for n in planner.body if isinstance(n,ast.FunctionDef)]
assert {n.name for n in functions}=={'clear','wireok','viaok','search'}
exec(compile(ast.Module(body=functions,type_ignores=[]),'existing_bounded_local_planner','exec'))
if fine:
    @functools.lru_cache(200000)
    def clear(net,l,x1,y1,x2,y2):
        sp=spacing[l]
        for bx in range((x1-sp)//1000,(x2+sp)//1000+1):
            for by in range((y1-sp)//1000,(y2+sp)//1000+1):
                for a,c,z,f,n in bucket.get((l,bx,by),[]):
                    if n==net:continue
                    dx=max(a-x2,x1-z,0);dy=max(c-y2,y1-f,0)
                    if dx*dx+dy*dy<sp*sp:return False
        return True
def rebuild():
    global bucket
    bucket=collections.defaultdict(list)
    for l,x1,y1,x2,y2,n in shapes:
        if l not in spacing:continue
        for x in range(x1//1000,x2//1000+1):
            for y in range(y1//1000,y2//1000+1):bucket[l,x,y].append((x1,y1,x2,y2,n))
    clear.cache_clear();wireok.cache_clear();viaok.cache_clear()
def check(tag):
    design.getTritonRoute().clearDesign();p=out/(tag+'.rpt')
    design.evalTclString(f'drt::check_drc -box {{1579000 630000 1615000 646000}} -output_file {p} -marker_name IndependentPlannedShort')
    text=p.read_text();m=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(m)==text.count('violation type:');return Counter(m)
current=check('baseline');assert sum(current.values())==7
plans=[
 ('net4749',[segment('met1',(1590450,635290),(1590450,635970)),segment('met1',(1590450,635970),(1593900,635970))],(1590450,635290,1),(1593900,635970,1)),
 ('net3179',[segment('met1',(1583095,639710),(1583095,640050)),segment('met1',(1583095,640050),(1583555,640050))],(1583095,639710,1),(1583555,640050,1)),
 ('net6342',[segment('met1',(1584470,638690),(1584470,639370)),segment('met1',(1584470,639370),(1586770,639370))],(1584470,638690,1),(1586770,639370,1)),
 ('_09264_',[segment('met2',(1610690,633250),(1612070,633250))],(1610690,633250,2),(1612070,633250,2)),
 ('net658',[segment('met2',(1586310,637330),(1586770,637330)),('T','M1M2_PR',1586770,637330)],(1586310,637330,2),(1586770,637330,1)),
]
accepted=[];attempts=[]
for name,cuts,start,end in plans:
    rebuild();net=b.findNet(name);w=net.getWire();original,ids=primitives(w);vid=via_ids(w)
    assert not Counter(cuts)-original
    # Bound each search to endpoints plus 5um; all geometry in that box is inventoried.
    data['region']=[min(start[0],end[0])-5060,min(start[1],end[1])-5100,max(start[0],end[0])+5060,max(start[1],end[1])+5100]
    assert data['region'][0]>=region[0] and data['region'][1]>=region[1] and data['region'][2]<=region[2] and data['region'][3]<=region[3]
    print('PLAN_ENDPOINTS',name,wireok(name,'met'+str(start[2]),*start[:2],*start[:2]),wireok(name,'met'+str(end[2]),*end[:2],*end[:2]),flush=True)
    path=search(name,start,end)
    if path is None:attempts.append({'net':name,'path_found':False});continue
    graph=odb.dbWireGraph();graph.decode(w)
    for q in cuts:graph.deleteEdge(graph.getEdge(ids[(q[1],q[2:4],q[4:6])] if q[0]=='S' else vid[q]))
    # Merge adjacent planar steps so line-end rules see the actual continuous path.
    compact=[]
    for edge in path:
        if compact and not edge['via'] and not compact[-1]['via']:
            prev=compact[-1];a,z=prev['from'],prev['to'];e=edge['to']
            if z==edge['from'] and a[2]==z[2]==e[2] and ((a[0]==z[0]==e[0]) or (a[1]==z[1]==e[1])):prev['to']=e;continue
        compact.append(dict(edge))
    added=Counter()
    for edge in compact:
        a,z=edge['from'],edge['to'];an=graph.createNode(*a[:2],tech.findLayer('met'+str(a[2])));zn=graph.createNode(*z[:2],tech.findLayer('met'+str(z[2])))
        if edge['via']:graph.createTechVia(an,zn,tech.findVia(edge['via']));added[('T',edge['via'],*a[:2])]+=1
        else:graph.createSegment(an,zn);added[segment('met'+str(a[2]),a[:2],z[:2])]+=1
    graph.encode(w);normalize_routes(w);restore_patches(w,original)
    assert primitives(w)[0]==original-Counter(cuts)+added
    missing,disconnected,_=connectivity(net);assert not missing and not disconnected,('Disconnected proposed path',name)
    observed=check(name);ok=not (observed-current) and sum(observed.values())<sum(current.values())
    attempts.append({'net':name,'path_found':True,'path':compact,'local_markers':sum(observed.values()),'accepted':ok});print('PLANNED_SHORT_RESULT',name,ok,sum(observed.values()),flush=True)
    if ok:
        accepted.append({'net':name,'removed':cuts,'added':list(added.elements())});current=observed
        shapes[:]=[q for q in shapes if q[-1]!=name];add_wire(net)
    else:
        odb.dbWire.destroy(w);w=odb.dbWire.create(net);w.append(rb.findNet(name).getWire());assert wires(b)[name]==oldw[name]
    (out/'progress.json').write_text(json.dumps({'attempts':attempts,'accepted_changes':accepted,'remaining_local_markers':sum(current.values()),'accepted_for_final':False},indent=2)+'\n')
changed={r['net'] for r in accepted};assert {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in oldw.items() if n not in changed}
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
name='short_paths_fine.odb' if fine else 'short_paths.odb'
native=Path('/runtime_final')/name;permanent=C/'inputs'/name;assert not native.exists() and not permanent.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,permanent.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
with native.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
with permanent.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
(out/'result.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':digest,'attempts':attempts,'accepted_changes':accepted,'remaining_local_markers':sum(current.values()),'all_changed_net_terminals_geometrically_connected':True,'all_other_wire_bytes_and_cells_graph_PG_guides_obstructions_unchanged':True,'accepted_for_final':False},indent=2)+'\n')
print('PLANNED_SHORT_SEARCH_COMPLETE',len(accepted),sum(current.values()),digest,flush=True)
