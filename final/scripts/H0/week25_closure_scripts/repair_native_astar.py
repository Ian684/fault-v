"""Repair one native crossing and residual antennas with higher-metal jumpers."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import fixed,wires,guides,obstructions,primitives,encode_fixed
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/runtime/antenna_native12.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==json.loads((C/'reports/antenna_iter12_probe.json').read_text())['source_sha256']
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
metal={'li1','met1','met2','met3','met4','met5'};width={l:tech.findLayer(l).getWidth() for l in metal}
for file,names in [(R/'scripts/search_manual_eco.py',{'normalize_routes'}),(R/'scripts/check_antenna_signal_connectivity.py',{'connectivity'})]:
    code=file.read_text();tree=ast.parse(code);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    text='\n'.join(ast.get_source_segment(code,n) for n in nodes)
    if 'connectivity' in names:
        needle='sum(diode for name,diode,i in terminals))';assert text.count(needle)==1;text=text.replace(needle,'sum(diode for name,diode,i in terminals),len({root(i) for i in range(len(shapes))}))')
    exec(compile(text,file.name,'exec'))
out=C/'reports/native_upper_f';out.mkdir(exist_ok=False);design.evalTclString('set_thread_count 2')
def install(n,g):
    encode_fixed(n.getWire(),g,tech,b);normalize_routes(n.getWire());assert primitives(n.getWire())[0]==g
def check(tag,roi):
    design.getTritonRoute().clearDesign();p=out/(tag+'.drc.rpt')
    design.evalTclString('drt::check_drc -box {'+' '.join(map(str,roi))+'} -output_file '+str(p)+' -marker_name HigherMetalRepair')
    text=p.read_text();markers=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(markers)==text.count('violation type:');return Counter(markers)
def connected(n):
    missing,disconnected,count,components=connectivity(n);return not missing and not disconnected and components==1
def piece(layer,a,z,e1=None,e2=None):
    assert a!=z and (a[0]==z[0] or a[1]==z[1]);a,z=sorted((a,z));h=width[layer]//2
    return ('S',layer,*a,*z,h if e1 is None else e1,h if e2 is None else e2)
via_name={1:'M1M2_PR',2:'M2M3_PR',3:'M3M4_PR',4:'M4M5_PR'}
def jumper(q,offset,span,top):
    base=int(q[1][-1]);a=(q[2],q[3]);z=(q[4],q[5]);vertical=a[0]==z[0]
    p=(a[0],a[1]+offset) if vertical else (a[0]+offset,a[1]);r=(p[0],p[1]+span) if vertical else (p[0]+span,p[1])
    added=Counter([piece(q[1],a,p,q[-2],width[q[1]]//2),piece(q[1],r,z,width[q[1]]//2,q[-1]),piece('met'+str(top),p,r)])
    for x,y in (p,r):
        for layer in range(base,top):
            v=via_name[layer];assert tech.findVia(v);added['T',v,x,y]+=1
    return added,p,r
attempts=[];repairs=[];counter=0
marker=json.loads((C/'reports/antenna_iter12_independent.json').read_text())['unresolved'];assert len(marker)==1 and marker[0]['type']=='Short'
marker=marker[0];layer=marker['layer'];assert layer in ('met1','met2');x1,y1,x2,y2=marker['bbox_dbu'];cx=(x1+x2)//2;cy=(y1+y2)//2
from native_metal_planner import repair_corner
record=repair_corner(design,db,b,out,normalize_routes,connectivity)
done=record is not None
if done:repairs.append(record)
for name in ([] if done else re.findall(r'net:([^\s]+)',marker['srcs'])):
    n=b.findNet(name);geometry=primitives(n.getWire())[0]
    candidates=[q for q in geometry if q[0]=='S' and q[1]==layer and min(q[2],q[4])-200<=cx<=max(q[2],q[4])+200 and min(q[3],q[5])-200<=cy<=max(q[3],q[5])+200]
    for q in candidates:
        length=abs(q[4]-q[2])+abs(q[5]-q[3]);position=cy-q[3] if q[2]==q[4] else cx-q[2]
        for span in (800,1200,2000,4000,6000):
            for shift in (0,-100,100,-200,200):
                offset=position-span//2+shift
                if offset<350 or offset+span>length-350 or not (offset+250<position<offset+span-250):continue
                for top in range(int(layer[-1])+1,5):
                    counter+=1;added,p,r=jumper(q,offset,span,top);trial=geometry-Counter([q])+added;install(n,trial)
                    roi=[min(p[0],r[0],x1)-4000,min(p[1],r[1],y1)-4000,max(p[0],r[0],x2)+4000,max(p[1],r[1],y2)+4000]
                    count=sum(check('short_'+str(counter),roi).values());conn=connected(n) if count==0 else False
                    attempts.append({'kind':'short','trial':counter,'net':name,'top':top,'native_local_DRC':count,'connected':conn})
                    print('NATIVE_SHORT_TRIAL',counter,name,top,count,conn,flush=True)
                    if count==0 and conn:repairs.append({'net':name,'kind':'short','original_segment':q,'cut_start':p,'cut_end':r,'bridge_layer':'met'+str(top)});done=True;break
                    install(n,geometry)
                if done:break
            if done:break
        if done:break
    if done:break
assert done,'No clean connected higher-metal crossing repair'
def antennas(tag):
    p=out/(tag+'.antenna.rpt');count=int(design.evalTclString('check_antennas -report_file '+str(p)));text=p.read_text();rows={};net=None;pin=None;layer=None
    for line in text.splitlines():
        m=re.match(r'Net:\s+(\S+)',line)
        if m:net=m[1]
        m=re.match(r'\s*Pin:\s+(\S+)',line)
        if m:pin=m[1]
        m=re.match(r'\s*Layer:\s+(\S+)',line)
        if m:layer=m[1]
        if '(VIOLATED)' in line:rows.setdefault(net,(pin,layer))
    assert len(rows)==count;return rows
violators=antennas('after_short')
for fix in range(4):
    if not violators:break
    name,(gate_pin,layer)=next(iter(violators.items()));assert layer in ('met1','met2')
    inst,pin=gate_pin.rsplit('/',1);gate=b.findInst(inst).findITerm(pin);gx,gy=gate.getInst().getLocation();ap=list(gate.getPrefAccessPoints());assert ap;ax,ay=ap[0].getPoint();gx+=ax;gy+=ay
    n=b.findNet(name);geometry=primitives(n.getWire())[0];base=int(layer[-1])
    dist=lambda q:abs(gx-min(max(gx,q[2]),q[4]))+abs(gy-min(max(gy,q[3]),q[5]))
    candidates=sorted([q for q in geometry if q[0]=='S' and q[1]==layer and abs(q[4]-q[2])+abs(q[5]-q[3])>=3500],key=dist);done=False
    for q in candidates[:16]:
        length=abs(q[4]-q[2])+abs(q[5]-q[3]);roi=[q[2]-4000,q[3]-4000,q[4]+4000,q[5]+4000]
        install(n,geometry);baseline=check('antenna_base_'+str(counter),roi)
        for span in (4000,2000,8000,15000):
            for offset in (700,1200,2000):
                if offset+span+500>length:continue
                for top in range(base+1,min(5,base+3)):
                    counter+=1;added,p,r=jumper(q,offset,span,top);trial=geometry-Counter([q])+added;install(n,trial)
                    count=sum((check('ant_'+str(counter),roi)-baseline).values());conn=connected(n) if count==0 else False;after=antennas('ant_'+str(counter)) if conn else violators
                    attempts.append({'kind':'antenna','trial':counter,'net':name,'top':top,'new_native_local_DRC':count,'connected':conn,'antenna_nets':len(after)})
                    (out/'progress.json').write_text(json.dumps({'repairs':repairs,'attempts':attempts,'accepted_for_final':False},indent=2)+'\n')
                    print('NATIVE_ANTENNA_TRIAL',counter,name,top,count,conn,len(after),flush=True)
                    if count==0 and conn and name not in after and set(after)<set(violators):
                        repairs.append({'net':name,'kind':'antenna','original_segment':q,'cut_start':p,'cut_end':r,'bridge_layer':'met'+str(top)});violators=after;done=True;break
                    install(n,geometry)
                if done:break
            if done:break
        if done:break
    assert done,('No clean connected antenna jumper',name)
assert not violators and fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
changed={r['net'] for r in repairs};assert {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in oldw.items() if n not in changed}
native=Path('/runtime_final/native_upper_f.odb');dest=C/'inputs/native_upper_f.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as f,dest.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(native)==sha(dest)
(out/'result.json').write_text(json.dumps({'output_sha256':sha(native),'source_native_sha256':sha(source),'antenna_nets':0,'passive_diodes_added':20,'repairs':repairs,'cells_graph_PG_guides_obstructions_unchanged':True,'all_unaffected_wire_bytes_preserved':True,'accepted_for_final':False,'scope':'Native pin accesses retained; only explicit higher-metal local bridges changed. Whole-source native/context DRC, connectivity, full GDS/core LVS and fresh electrical/activity checks remain mandatory.'},indent=2)+'\n')
print('NATIVE_UPPER_CANDIDATE_READY',sha(native),flush=True)
