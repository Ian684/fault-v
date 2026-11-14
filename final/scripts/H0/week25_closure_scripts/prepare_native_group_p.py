from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,encode_fixed
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/runtime_final/native_group_m.odb');reference=Path('/runtime_final/antenna_stubs_f.odb');plan=json.loads((C/'controls/antenna_o_replay.json').read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==plan['source_M_sha256'] and sha(reference)==plan['source_F_sha256']
verified=json.loads((C/'reports/native_m_geometry_verified.json').read_text());assert verified['source_sha256']==sha(source) and verified['independent_native_context_DRC']==0
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech();rd,rb=load(reference)
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b);assert before==fixed(rb) and oldg==guides(rb) and oldo==obstructions(rb)
metal={'li1','met1','met2','met3','met4','met5'};width={l:tech.findLayer(l).getWidth() for l in metal}
for file,names in [(R/'scripts/search_manual_eco.py',{'normalize_routes'}),(R/'scripts/check_antenna_signal_connectivity.py',{'connectivity'})]:
    text=file.read_text();tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    text='\n'.join(ast.get_source_segment(text,n) for n in nodes)
    if 'connectivity' in names:
        needle='sum(diode for name,diode,i in terminals))';assert text.count(needle)==1;text=text.replace(needle,'sum(diode for name,diode,i in terminals),len({root(i) for i in range(len(shapes))}))')
    exec(compile(text,file.name,'exec'))
def piece(layer,a,z,e1,e2):
    a,z=sorted((a,z));return ('S',layer,*a,*z,e1,e2)
for row in plan['repairs']:
    n=b.findNet(row['net']);g=primitives(n.getWire())[0];q=tuple(row['original_segment']);assert g[q]==1 and row['bridge_layer']=='met3'
    p,z=map(tuple,(row['cut_start'],row['cut_end']));a=q[2:4];end=q[4:6]
    add=Counter([piece('met2',a,p,q[-2],70),piece('met2',z,end,70,q[-1]),piece('met3',p,z,150,150)])
    for x,y in (p,z):add['T','M2M3_PR',x,y]+=1
    target=g-Counter([q])+add;encode_fixed(n.getWire(),target,tech,b);normalize_routes(n.getWire());assert primitives(n.getWire())[0]==target
n=b.findNet('net6330');g=primitives(n.getWire())[0];ref=primitives(rb.findNet('net6330').getWire())[0]
assert g-Counter(map(tuple,plan['M_6330_branch']['added_primitives']))==ref-Counter(map(tuple,plan['F_6330_branch']['added_primitives']))
odb.dbWire.destroy(n.getWire());w=odb.dbWire.create(n);w.append(rb.findNet('net6330').getWire());assert primitives(w)[0]==ref
changed={'net6033','_10658_','net6330'}
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo and {n:v for n,v in wires(b).items() if n not in changed}=={n:v for n,v in oldw.items() if n not in changed}
out=C/'reports/native_group_p';out.mkdir(exist_ok=False);design.evalTclString('set_thread_count 2')
connected={}
for name in sorted(changed):
    missing,disconnected,diodes,components=connectivity(b.findNet(name));assert not missing and not disconnected and components==1,(name,missing,disconnected,components)
    connected[name]={'components':components,'diode_terminals':diodes}
ant=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')));assert ant==0,ant
p=out/'global.drc.rpt';design.getTritonRoute().clearDesign();design.evalTclString('drt::check_drc -output_file '+str(p)+' -marker_name AntennaReplayO')
text=p.read_text();markers=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(markers)==text.count('violation type:')
assert all(k in ('NS Metal','Metal Spacing') and s.count('net:')==1 and box.endswith('on Layer li1') for k,s,box in markers),'Raw geometry has non-eligible markers'
native=Path('/runtime_final/native_group_p.odb');dest=C/'inputs/native_group_p.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as f,dest.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
assert sha(native)==sha(dest)
(out/'result.json').write_text(json.dumps({'source_sha256':sha(source),'net6330_reference_sha256':sha(reference),'output_sha256':sha(native),'antenna_nets':ant,'raw_native_markers':len(markers),'changed_nets_connectivity':connected,'replayed_antenna_repairs':plan['repairs'],'net6330_wire_primitive_geometry_equals_checked_F_source':True,'cells_graph_PG_guides_obstructions_unchanged':True,'all_unaffected_wire_bytes_preserved':True,'passive_diodes_added':20,'accepted_for_final':False,'scope':'Exact replay of two successful native/antenna jumpers, plus the complete net6330 route from the independently checked earlier F source. Full independent/context DRC, all-net connectivity, final GDS/core LVS and all electrical/activity/IR/fill gates remain mandatory.'},indent=2)+'\n')
print('NATIVE_O_ANTENNA_ZERO_CANDIDATE_READY',ant,len(markers),sha(native),flush=True)
