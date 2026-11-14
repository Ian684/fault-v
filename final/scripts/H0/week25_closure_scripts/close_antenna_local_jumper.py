"""Keep checked diode branches and reduce one residual M2 antenna component locally."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,encode_fixed
C=Path('/work/week25_closure');R=C.parent/'routing'
t=Tech();design=Design(t);design.readDb('/runtime_final/antenna_ready.odb');db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
rd,rb=load('/runtime_final/focus_pg.odb');before=fixed(b);oldg=guides(b);oldo=obstructions(b)
access=json.loads((C/'reports/antenna_access.json').read_text())
for name in access['cleared_signal_nets']:
    n=b.findNet(name);assert not n.getWire();w=odb.dbWire.create(n);w.append(rb.findNet(name).getWire())
assert wires(b)==wires(rb)
width={l:tech.findLayer(l).getWidth() for l in ('li1','met1','met2','met3','met4','met5')}
layername=lambda n:'li1' if n==0 else 'met'+str(n)
for file,names in [(C/'scripts/append_antenna_stubs_f.py',{'append','append_patches'}),(R/'scripts/search_manual_eco.py',{'normalize_routes'})]:
    tree=ast.parse(file.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file.name,'exec'))
rows=json.loads((C/'reports/antenna_stubs_h/incomplete.json').read_text())['accepted']
assert len(rows)==19 and all(r['net']!='net6033' for r in rows)
rows+=[r for r in json.loads((C/'reports/antenna_stubs_f/result.json').read_text())['accepted'] if r['net']=='net6033'];assert len(rows)==20
for row in rows:
    net=b.findNet(row['net']);added=append(net,row['path']);patches=[tuple(q) for q in row['added_primitives'] if q[0]=='R']
    if patches:added+=append_patches(net,patches)
    assert added==Counter(map(tuple,row['added_primitives']))
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
out=C/'reports/antenna_jumper';out.mkdir(exist_ok=False);design.evalTclString('set_thread_count 2')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def antenna(tag):return int(design.evalTclString('check_antennas -report_file '+str(out/(tag+'.antenna.rpt'))))
base_ant=antenna('baseline');assert base_ant==1,base_ant
base=Path('/runtime_final/antenna_jumper_base.odb');odb.write_db(db,str(base));dest=C/'inputs/antenna_jumper_base.odb';assert not dest.exists()
with base.open('rb') as f,dest.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(base)==sha(dest)
original_wires=wires(b);net=b.findNet('net6033');geometry=primitives(net.getWire())[0]
gate=b.findInst('_39369_').findITerm('B1');gx,gy=gate.getInst().getLocation();point=list(gate.getPrefAccessPoints())[0].getPoint();gx+=point[0];gy+=point[1]
def distance(q):
    return abs(gx-min(max(gx,q[2]),q[4]))+abs(gy-min(max(gy,q[3]),q[5]))
segments=sorted([q for q in primitives(rb.findNet('net6033').getWire())[0] if q[0]=='S' and q[1]=='met2' and abs(q[4]-q[2])+abs(q[5]-q[3])>=3500],key=distance)
assert segments
def piece(layer,a,z,e1=None,e2=None):
    assert a!=z and (a[0]==z[0] or a[1]==z[1]);a,z=sorted((a,z));h=width[layer]//2
    return ('S',layer,*a,*z,h if e1 is None else e1,h if e2 is None else e2)
def install(g):
    encode_fixed(net.getWire(),g,tech,b);normalize_routes(net.getWire());assert primitives(net.getWire())[0]==g
def check(tag,roi):
    design.getTritonRoute().clearDesign();p=out/(tag+'.drc.rpt')
    design.evalTclString('drt::check_drc -box {'+' '.join(map(str,roi))+'} -output_file '+str(p)+' -marker_name AntennaJumper')
    text=p.read_text();markers=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(markers)==text.count('violation type:');return Counter(markers)
attempts=[];accepted=None;index=0
for q in segments[:16]:
    a=(q[2],q[3]);z=(q[4],q[5]);length=abs(z[0]-a[0])+abs(z[1]-a[1]);vertical=a[0]==z[0]
    roi=[a[0]-4000,a[1]-4000,z[0]+4000,z[1]+4000];install(geometry);baseline=check('segment_'+str(index),roi)
    for span in (4000,2000,8000,15000):
        for offset in (700,1200,2000):
            if offset+span+500>length:continue
            p=(a[0],a[1]+offset) if vertical else (a[0]+offset,a[1]);r=(p[0],p[1]+span) if vertical else (p[0]+span,p[1])
            for top in ('met3','met4'):
                index+=1;added=Counter([piece('met2',a,p,q[-2],70),piece('met2',r,z,70,q[-1]),piece(top,p,r)])
                for x,y in (p,r):
                    assert tech.findVia('M2M3_PR');added['T','M2M3_PR',x,y]+=1
                    if top=='met4':assert tech.findVia('M3M4_PR');added['T','M3M4_PR',x,y]+=1
                trial=geometry-Counter([q])+added;install(trial);markers=check('trial_'+str(index),roi)
                new=sum((markers-baseline).values());ant=None
                if not new:ant=antenna('trial_'+str(index))
                row={'trial':index,'original_segment':q,'cut_start':p,'cut_end':r,'bridge_layer':top,'new_native_local_markers':new,'antenna_nets':ant};attempts.append(row)
                (out/'progress.json').write_text(json.dumps({'source_base_sha256':sha(base),'baseline_antenna_nets':base_ant,'attempts':attempts,'accepted_for_final':False},indent=2)+'\n')
                print('ANTENNA_JUMPER_TRIAL',index,top,'new DRC',new,'antenna',ant,flush=True)
                if new==0 and ant==0:accepted=row;break
                if index>=160:break
            if accepted or index>=160:break
        if accepted or index>=160:break
    if accepted or index>=160:break
assert accepted,'No independently clean antenna jumper within search bound'
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
assert {n:v for n,v in wires(b).items() if n!='net6033'}=={n:v for n,v in original_wires.items() if n!='net6033'}
native=Path('/runtime_final/antenna_jumper.odb');target=C/'inputs/antenna_jumper.odb';assert not native.exists() and not target.exists();odb.write_db(db,str(native))
with native.open('rb') as f,target.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(native)==sha(target)
(out/'result.json').write_text(json.dumps({'output_sha256':sha(native),'source_base_sha256':sha(base),'antenna_nets':0,'passive_diodes_added':20,'accepted_local_jumper':accepted,'cells_graph_PG_guides_obstructions_unchanged':True,'only_net6033_copper_changed_from_checked_branch_base':True,'accepted_for_final':False,'scope':'Local higher-metal jumper with native local geometry and whole-chip antenna zero. Full/context DRC, every physical signal component and all final gates remain required.'},indent=2)+'\n')
print('ANTENNA_JUMPER_CANDIDATE_READY',sha(native),flush=True)
