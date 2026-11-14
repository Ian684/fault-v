"""Bounded local proposals for the three independently confirmed crossing pairs."""
from pathlib import Path
from collections import Counter,defaultdict
from openroad import Tech,Design
import ast,hashlib,json,re,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/route_b/1-openroad-detailedrouting/native_final.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=json.loads((C/'reports/short_b_final_independent.json').read_text());assert proof['unresolved_count']==4 and sha(source)==proof['odb_sha256']
conn=json.loads((C/'reports/short_b_final_all_connectivity.json').read_text());assert conn['source_sha256']==sha(source) and conn['all_signal_geometry_connected']
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech();rd,rb=load(source)
metal={'li1','met1','met2','met3','met4','met5'}
for file,names in [(R/'scripts/search_manual_eco.py',{'normalize_routes','restore_patches'}),(R/'scripts/check_antenna_signal_connectivity.py',{'connectivity'}),(C/'scripts/search_short_bridges.py',{'segment'})]:
    tree=ast.parse(file.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names;exec(compile(ast.Module(body=nodes,type_ignores=[]),file.name,'exec'))
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b);out=C/'reports/final_crossings_a';out.mkdir(exist_ok=False)
design.evalTclString('set_thread_count 2');attempts=[];accepted=[]
def check(tag):
    design.getTritonRoute().clearDesign();p=out/(tag+'.rpt');design.evalTclString(f'drt::check_drc -box {{1578000 628000 1622000 642000}} -output_file {p} -marker_name FinalCrossingTrial')
    text=p.read_text();rows=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(rows)==text.count('violation type:');return Counter(rows)
current=check('baseline');assert sum(current.values())==4
def all_ids(w):
    d=odb.dbWireDecoder();d.begin(w);point=None;nodes={};ids={}
    while True:
        op=d.next()
        if op==d.END_DECODE:break
        if op in (d.POINT,d.POINT_EXT):point=tuple((d.getPoint_ext() if op==d.POINT_EXT else d.getPoint())[:2]);nodes[d.getJunctionId()]=point
        elif op==d.JUNCTION:point=nodes[d.getJunctionValue()]
        elif op in (d.TECH_VIA,d.VIA):
            v=d.getTechVia() if op==d.TECH_VIA else d.getVia();q=('T' if op==d.TECH_VIA else 'V',v.getName(),*point);assert q not in ids;ids[q]=d.getJunctionId();nodes[d.getJunctionId()]=point
    return ids
plans=[]
# Slide the M2-to-M1 transition above the crossing while retaining both far endpoints.
cuts=[segment('met2',(1591830,631380),(1591830,636310)),('T','M1M2_PR',1591830,636310),segment('met1',(1591830,636310),(1591830,637670))]
for y in (636990,637330,637670,637160,637500,637075,637245,637415):
    plans.append(('net4985',cuts,[(1591830,631380,'met2'),(1591830,y,'met2'),(1591830,y,'met1'),(1591830,637670,'met1')],y))
# Move the short vertical step left of the other net's corner.
cuts=[segment('met2',(1613910,631550),(1614325,631550)),segment('met2',(1614325,631550),(1614325,632060)),segment('met2',(1614325,632060),(1614370,632060))]
for delta in (-280,-300,-320,-340,-460,-600,-920):
    x=1614325+delta;plans.append(('_03545_',cuts,[(1613910,631550,'met2'),(x,631550,'met2'),(x,632060,'met2'),(1614370,632060,'met2')],delta))
# The opposing horizontal extends 3.22um, so a whole-route-track nudge cannot clear it.
cuts=[segment('met2',(1610690,632910),(1611780,632910)),segment('met2',(1611780,632910),(1611780,634270)),segment('met2',(1611610,634270),(1611780,634270))]
for delta in (-3390,-3680,-3850,-4080,-4310,-4600,-5060,-5520):
    x=1611780+delta;plans.append(('net4469',cuts,[(1610690,632910,'met2'),(x,632910,'met2'),(x,634270,'met2'),(1611610,634270,'met2')],delta))
done=set()
for index,(name,cuts,path,value) in enumerate(plans):
    if name in done:continue
    n=b.findNet(name);w=n.getWire();original,ids=primitives(w);assert not (Counter(cuts)-original),('Source path changed',name)
    saved=odb.dbWireGraph();saved.decode(w);vid=all_ids(w);g=odb.dbWireGraph();g.decode(w)
    for q in cuts:g.deleteEdge(g.getEdge(ids[(q[1],q[2:4],q[4:6])] if q[0]=='S' else vid[q]))
    added=Counter()
    for a,z in zip(path,path[1:]):
        if a==z:continue
        an=g.createNode(*a[:2],tech.findLayer(a[2]));zn=g.createNode(*z[:2],tech.findLayer(z[2]))
        if a[2]==z[2]:g.createSegment(an,zn);added[segment(a[2],a[:2],z[:2])]+=1
        else:g.createTechVia(an,zn,tech.findVia('M1M2_PR'));added[('T','M1M2_PR',*a[:2])]+=1
    g.encode(w);normalize_routes(w);restore_patches(w,original)
    assert primitives(w)[0]==original-Counter(cuts)+added,('Unexpected geometry delta',name,value)
    missing,disconnected,_=connectivity(n)
    if missing or disconnected:observed=current.copy();ok=False
    else:observed=check(f'{index:02}_{name}');ok=not(observed-current) and sum(observed.values())<sum(current.values())
    attempts.append({'net':name,'coordinate_or_delta_dbu':value,'local_markers':sum(observed.values()),'accepted':ok});print('FINAL_CROSSING_ATTEMPT',attempts[-1],flush=True)
    if ok:accepted.append({'net':name,'removed':cuts,'added':list(added.elements())});current=observed;done.add(name)
    else:odb.dbWire.destroy(w);w=odb.dbWire.create(n);w.append(rb.findNet(name).getWire());assert wires(b)[name]==oldw[name]
    assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
    (out/'progress.json').write_text(json.dumps({'attempts':attempts,'accepted_changes':accepted,'remaining_local_markers':sum(current.values()),'accepted_for_final':False},indent=2)+'\n')
changed={r['net'] for r in accepted};assert {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in oldw.items() if n not in changed}
native=Path('/runtime_final/final_crossings.odb');permanent=C/'inputs/final_crossings.odb';assert not native.exists() and not permanent.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,permanent.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(permanent)
(out/'result.json').write_text(json.dumps({'source_sha256':sha(source),'output_sha256':sha(native),'attempts':attempts,'accepted_changes':accepted,'remaining_local_markers':sum(current.values()),'all_cells_graph_PG_guides_obstructions_and_unaffected_wire_bytes_preserved':True,'accepted_for_final':False,'scope':'Local bounded transition/jog changes only. Only strict no-new-marker improvements retained. All geometry changes lie inside checked box with 2um margin. Independent full/context DRC plus all-net copper/pin connectivity and final electrical/LVS/antenna gates still required.'},indent=2)+'\n');print('FINAL_CROSSING_TRIAL_COMPLETE',len(accepted),sum(current.values()),sha(native),flush=True)
