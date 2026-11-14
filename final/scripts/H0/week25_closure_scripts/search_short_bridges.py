"""Bounded local layer changes; accept only strict independent DRC improvements."""
from pathlib import Path
from collections import Counter,defaultdict
from openroad import Tech,Design
import ast,hashlib,json,re,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/runtime/focus_final.odb')
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
metal={'li1','met1','met2','met3','met4','met5'}
for file,names in [('search_manual_eco.py',{'normalize_routes','restore_patches'}),('check_antenna_signal_connectivity.py',{'connectivity'})]:
    tree=ast.parse((R/'scripts'/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
design.evalTclString('set_thread_count 2')
out=C/'reports/short_bridges_b';out.mkdir(exist_ok=False)
roi='1579000 630000 1615000 646000'
def check(tag):
    design.getTritonRoute().clearDesign();p=out/(tag+'.rpt')
    design.evalTclString(f'drt::check_drc -box {{{roi}}} -output_file {p} -marker_name IndependentShortBridge')
    text=p.read_text();items=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text)
    assert len(items)==text.count('violation type:')
    return Counter(items)
baseline=check('baseline');assert len(list(baseline.elements()))==7,baseline
def segment(layer,a,z):
    assert (a[0]==z[0]) != (a[1]==z[1]);a,z=sorted((a,z));h=tech.findLayer(layer).getWidth()//2
    return ('S',layer,*a,*z,h,h)
def via_ids(w):
    d=odb.dbWireDecoder();d.begin(w);point=None;result={}
    while True:
        op=d.next()
        if op==d.END_DECODE:break
        if op in (d.POINT,d.POINT_EXT):point=tuple((d.getPoint_ext() if op==d.POINT_EXT else d.getPoint())[:2])
        elif op in (d.TECH_VIA,d.VIA):
            v=d.getTechVia() if op==d.TECH_VIA else d.getVia();q=('T' if op==d.TECH_VIA else 'V',v.getName(),*point)
            assert q not in result;result[q]=d.getJunctionId()
    return result
via_options=[v for v in tech.getVias() if v.getBottomLayer().getName()=='met1' and v.getTopLayer().getName()=='met2' and len([q for q in v.getBoxes() if q.getTechLayer().getName()=='via'])==1]
assert via_options
via_options.sort(key=lambda v:(v.getName()!='M1M2_PR',v.getName()))
# Each replacement keeps the two endpoints of a connected local path.
plans=[
 ('net4749',[segment('met1',(1590450,635290),(1590450,635970))],[(1590450,635290),(1590450,635970)],'met1','met2'),
 ('net3179',[segment('met1',(1583095,639710),(1583095,640050)),segment('met1',(1583095,640050),(1583555,640050))],[(1583095,639710),(1583095,640050),(1583555,640050)],'met1','met2'),
 ('net6342',[segment('met1',(1584470,638690),(1584470,639370)),segment('met1',(1584470,639370),(1586770,639370))],[(1584470,638690),(1584470,639370),(1586770,639370)],'met1','met2'),
 ('_09264_',[segment('met2',(1610690,633250),(1612070,633250))],[(1610690,633250),(1612070,633250)],'met2','met1'),
]
attempts=[];accepted=[];current=baseline
for name,cuts,points,oldlayer,newlayer in plans:
    net=b.findNet(name);w=net.getWire();original,ids=primitives(w);assert not (Counter(cuts)-original)
    saved=odb.dbWireGraph();saved.decode(w);found=False
    for index,via in enumerate(via_options[:8]):
        saved.encode(w);normalize_routes(w);restore_patches(w,original);assert primitives(w)[0]==original
        graph=odb.dbWireGraph();graph.decode(w)
        for q in cuts:graph.deleteEdge(graph.getEdge(ids[(q[1],q[2:4],q[4:6])]))
        coords=[(*points[0],oldlayer)]+[(*p,newlayer) for p in points]+[(*points[-1],oldlayer)]
        nodes=[graph.createNode(x,y,tech.findLayer(layer)) for x,y,layer in coords]
        for i in range(len(nodes)-1):
            if coords[i][2]==coords[i+1][2]:graph.createSegment(nodes[i],nodes[i+1])
            else:graph.createTechVia(nodes[i],nodes[i+1],via)
        graph.encode(w);normalize_routes(w);restore_patches(w,original)
        added=Counter(segment(newlayer,a,z) for a,z in zip(points,points[1:]));added.update(('T',via.getName(),*p) for p in (points[0],points[-1]))
        assert primitives(w)[0]==original-Counter(cuts)+added,('Unexpected geometry delta',name)
        missing,disconnected,_=connectivity(net);assert not missing and not disconnected,('Connectivity lost',name)
        observed=check(f'{name}_{index}');ok=not (observed-current) and sum(observed.values())<sum(current.values())
        attempts.append({'net':name,'via':via.getName(),'markers':sum(observed.values()),'accepted':ok})
        print('BRIDGE_ATTEMPT',attempts[-1],flush=True)
        if ok:
            accepted.append({'net':name,'removed':cuts,'added':list(added.elements())});current=observed;found=True;break
    if not found:
        saved.encode(w);normalize_routes(w);restore_patches(w,original);assert primitives(w)[0]==original
    assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
    if found:
        native=Path('/runtime_final/short_bridges_progress.odb');odb.write_db(db,str(native))
    (out/'progress.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'attempts':attempts,'accepted_changes':accepted,'remaining_local_markers':sum(current.values()),'accepted_for_final':False},indent=2)+'\n')
# Move the M1/M2 transition away from the other net's M2 vertical wire.
name='net658';net=b.findNet(name);w=net.getWire();original,ids=primitives(w);v_ids=via_ids(w)
cut=segment('met2',(1586310,637330),(1586770,637330));oldvia=('T','M1M2_PR',1586770,637330)
assert original[cut]==1 and original[oldvia]==1
saved=odb.dbWireGraph();saved.decode(w);graph=odb.dbWireGraph();graph.decode(w)
graph.deleteEdge(graph.getEdge(ids[(cut[1],cut[2:4],cut[4:6])]))
graph.deleteEdge(graph.getEdge(v_ids[oldvia]))
a=graph.createNode(1586310,637330,tech.findLayer('met2'));z=graph.createNode(1586310,637330,tech.findLayer('met1'));e=graph.createNode(1586770,637330,tech.findLayer('met1'))
graph.createTechVia(a,z,tech.findVia('M1M2_PR'));graph.createSegment(z,e)
graph.encode(w);normalize_routes(w);restore_patches(w,original)
added=Counter([segment('met1',(1586310,637330),(1586770,637330)),('T','M1M2_PR',1586310,637330)])
assert primitives(w)[0]==original-Counter([cut,oldvia])+added
missing,disconnected,_=connectivity(net);assert not missing and not disconnected
observed=check('net658');ok=not (observed-current) and sum(observed.values())<sum(current.values())
attempts.append({'net':name,'markers':sum(observed.values()),'accepted':ok});print('BRIDGE_ATTEMPT',attempts[-1],flush=True)
if ok:accepted.append({'net':name,'removed':[cut,oldvia],'added':list(added.elements())});current=observed
else:saved.encode(w);normalize_routes(w);restore_patches(w,original);assert primitives(w)[0]==original
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
changed={r['net'] for r in accepted};assert {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in oldw.items() if n not in changed}
native=Path('/runtime_final/short_bridges.odb');odb.write_db(db,str(native))
import shutil
permanent=C/'inputs/short_bridges.odb';assert not permanent.exists()
with native.open('rb') as inp,permanent.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
with native.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
with permanent.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
(out/'result.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'output_sha256':digest,'attempts':attempts,'accepted_changes':accepted,'remaining_local_markers':sum(current.values()),'all_original_terminals_of_changed_nets_connected':True,'cells_graph_PG_guides_obstructions_and_other_wires_unchanged':True,'accepted_for_final':False,'scope':'Bounded geometric short repairs only; independent full DRC, antenna, LVS and fresh extraction still required.'},indent=2)+'\n')
print('BRIDGE_SEARCH_COMPLETE',len(accepted),sum(current.values()),digest,flush=True)
