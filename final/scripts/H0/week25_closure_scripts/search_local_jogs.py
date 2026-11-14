"""Bounded three-segment jog shifts; only strict whole-chip DRC improvements survive."""
from pathlib import Path
from collections import Counter,defaultdict
from openroad import Tech,Design
import ast,hashlib,json,re,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/route_b/1-openroad-detailedrouting/drt_iter20.odb')
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech();rd,rb=load(source)
metal={'li1','met1','met2','met3','met4','met5'}
for file,names in [(R/'scripts/search_manual_eco.py',{'normalize_routes','restore_patches'}),(R/'scripts/check_antenna_signal_connectivity.py',{'connectivity'}),(C/'scripts/search_short_bridges.py',{'segment'})]:
    tree=ast.parse(file.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names;exec(compile(ast.Module(body=nodes,type_ignores=[]),file.name,'exec'))
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b);design.evalTclString('set_thread_count 2')
out=C/'reports/local_jogs_a';out.mkdir(exist_ok=False);attempts=[];accepted=[];evaluations=0
def check(tag):
    design.getTritonRoute().clearDesign();p=out/(tag+'.rpt');design.evalTclString(f'drt::check_drc -output_file {p} -marker_name IndependentJog')
    text=p.read_text();pattern=r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = \(([-0-9.]+), ([-0-9.]+)\) - \(([-0-9.]+), ([-0-9.]+)\) on Layer ([^\n]+)'
    rows=[tuple(m) for m in re.findall(pattern,text)];assert len(rows)==text.count('violation type:');return Counter(rows)
current=check('baseline');baseline=current.copy();assert sum(v for q,v in current.items() if q[-1]!='li1')==9
def restore(name):
    n=b.findNet(name);odb.dbWire.destroy(n.getWire());w=odb.dbWire.create(n);w.append(rb.findNet(name).getWire());assert wires(b)[name]==oldw[name]
def degree(shapes,layer,point):
    n=0
    for q in shapes:
        if q[0]=='S' and q[1]==layer and point in (q[2:4],q[4:6]):n+=1
        elif q[0] in ('T','V') and q[2:4]==point:
            via=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1])
            if layer in (via.getBottomLayer().getName(),via.getTopLayer().getName()):n+=1
    return n
done=set()
for marker in list(baseline):
    if marker[-1]=='li1' or marker not in current:continue
    layer=marker[-1];x1,y1,x2,y2=[round(float(v)*1000) for v in marker[2:6]]
    for name in re.findall(r'net:([^\s]+)',marker[1]):
        if name in done or name in ('VPWR','VGND'):continue
        net=b.findNet(name);assert net and net.getWire() and net.getNonDefaultRule() is None
        w=net.getWire();original,ids=primitives(w);saved=odb.dbWireGraph();saved.decode(w);found=False
        candidates=[]
        for q in original:
            if q[0]!='S' or q[1]!=layer:continue
            a,z=q[2:4],q[4:6];vertical=a[0]==z[0]
            if abs(a[0]-z[0])+abs(a[1]-z[1])>20000:continue
            if not(min(a[0],z[0])-160<=x2 and max(a[0],z[0])+160>=x1 and min(a[1],z[1])-160<=y2 and max(a[1],z[1])+160>=y1):continue
            if degree(original,layer,a)!=2 or degree(original,layer,z)!=2:continue
            adjacent=[]
            for point in (a,z):
                rows=[v for v in original if v[0]=='S' and v[1]==layer and v!=q and point in (v[2:4],v[4:6]) and (v[2]==v[4])!=vertical]
                if len(rows)!=1:break
                adjacent.append(rows[0])
            if len(adjacent)==2:candidates.append((q,*adjacent))
        for q,left,right in candidates:
            a,z=q[2:4],q[4:6];vertical=a[0]==z[0];pitch=460 if vertical else 340
            af=left[4:6] if left[2:4]==a else left[2:4];zf=right[4:6] if right[2:4]==z else right[2:4]
            for step in (1,-1,2,-2,3,-3,4,-4):
                if evaluations>=60:break
                saved.encode(w);normalize_routes(w);restore_patches(w,original);assert primitives(w)[0]==original
                delta=step*pitch;an=(a[0]+delta,a[1]) if vertical else (a[0],a[1]+delta);zn=(z[0]+delta,z[1]) if vertical else (z[0],z[1]+delta)
                if an==af or zn==zf:continue
                graph=odb.dbWireGraph();graph.decode(w)
                for cut in (q,left,right):graph.deleteEdge(graph.getEdge(ids[(cut[1],cut[2:4],cut[4:6])]))
                coords=[af,an,zn,zf];nodes=[graph.createNode(*p,tech.findLayer(layer)) for p in coords]
                for i in range(3):graph.createSegment(nodes[i],nodes[i+1])
                graph.encode(w);normalize_routes(w);restore_patches(w,original)
                added=Counter(segment(layer,a,z) for a,z in zip(coords,coords[1:]));expected=original-Counter((q,left,right))+added
                if primitives(w)[0]!=expected:continue
                missing,disconnected,_=connectivity(net)
                if missing or disconnected:continue
                observed=check(f'trial_{evaluations:02}');evaluations+=1;ok=not(observed-current) and sum(observed.values())<sum(current.values())
                attempts.append({'net':name,'delta_dbu':delta,'layer':layer,'raw_markers':sum(observed.values()),'accepted':ok});print('LOCAL_JOG_ATTEMPT',attempts[-1],flush=True)
                if ok:
                    accepted.append({'net':name,'removed':[q,left,right],'added':list(added.elements())});current=observed;found=True;done.add(name);break
            if found or evaluations>=60:break
        if not found:restore(name)
        assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
        (out/'progress.json').write_text(json.dumps({'attempts':attempts,'accepted_changes':accepted,'raw_markers':sum(current.values()),'remaining_non_li1':sum(v for q,v in current.items() if q[-1]!='li1'),'accepted_for_final':False},indent=2)+'\n')
        if evaluations>=60:break
    if evaluations>=60:break
changed={r['net'] for r in accepted};assert {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in oldw.items() if n not in changed}
native=Path('/runtime_final/local_jogs.odb');permanent=C/'inputs/local_jogs.odb';assert not native.exists() and not permanent.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,permanent.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(native)==sha(permanent)
(out/'result.json').write_text(json.dumps({'source_snapshot_sha256':sha(source),'output_sha256':sha(native),'attempts':attempts,'accepted_changes':accepted,'remaining_raw_markers':sum(current.values()),'remaining_non_li1':sum(v for q,v in current.items() if q[-1]!='li1'),'cells_graph_PG_guides_obstructions_and_other_wire_bytes_unchanged':True,'accepted_for_final':False,'scope':'Bounded three-segment jog changes only; each retained change strictly reduces whole-chip native DRC without new markers and preserves every signal terminal of that net. Independent full/context DRC plus all-net connectivity and all final gates still required.'},indent=2)+'\n')
print('LOCAL_JOG_SEARCH_COMPLETE',len(accepted),sum(v for q,v in current.items() if q[-1]!='li1'),sha(native),flush=True)
