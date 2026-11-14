"""Fill the independently reported same-net M1 gap without changing any other wire."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/runtime/signal_polished.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=json.loads((C/'reports/wide_b_independent.json').read_text());assert sha(source)==proof['odb_sha256'] and proof['unresolved_count']==3
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech();rd,rb=load(source)
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b);metal={'li1','met1','met2','met3','met4','met5'}
tree=ast.parse((R/'scripts/check_antenna_signal_connectivity.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='connectivity');exec(compile(ast.Module(body=[node],type_ignores=[]),'existing_connectivity','exec'))
out=C/'reports/wide_notch_b';out.mkdir(exist_ok=False);design.evalTclString('set_thread_count 2')
def check(tag):
    design.getTritonRoute().clearDesign();p=out/(tag+'.rpt');design.evalTclString(f'drt::check_drc -box {{1575000 620000 1630000 662000}} -output_file {p} -marker_name WideNotchTrial')
    text=p.read_text();rows=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(rows)==text.count('violation type:');return Counter(rows)
current=check('baseline');assert sum(current.values())==3
net=b.findNet('net9703');original=primitives(net.getWire())[0];attempts=[];accepted=[]
for k,box in enumerate([(1612900,648430,1612925,648625),(1612890,648425,1612930,648630),(1612835,648365,1612990,648690)]):
    w=net.getWire();enc=odb.dbWireEncoder();enc.append(w);x1,y1,x2,y2=box;enc.newPath(tech.findLayer('met1'),'ROUTED');enc.addPoint(x1,y1);enc.addRect(0,0,x2-x1,y2-y1);enc.end()
    patch=('R','met1',*box);assert primitives(w)[0]==original+Counter([patch])
    missing,disconnected,_=connectivity(net);assert not missing and not disconnected
    observed=check(str(k));ok=not(observed-current) and sum(observed.values())<sum(current.values());attempts.append({'box':box,'markers':sum(observed.values()),'accepted':ok});print('NOTCH_PATCH',attempts[-1],flush=True)
    if ok:accepted.append(patch);current=observed;break
    odb.dbWire.destroy(w);w=odb.dbWire.create(net);w.append(rb.findNet('net9703').getWire());assert wires(b)['net9703']==oldw['net9703']
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
assert {n:v for n,v in wires(b).items() if n!='net9703'}=={n:v for n,v in oldw.items() if n!='net9703'}
native=Path('/runtime_final/wide_notch_b.odb');dest=C/'inputs/wide_notch_b.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(dest)
(out/'result.json').write_text(json.dumps({'source_sha256':sha(source),'output_sha256':sha(native),'attempts':attempts,'accepted_patch':accepted,'remaining_local_markers':sum(current.values()),'all_cells_graph_PG_guides_obstructions_and_other_wire_bytes_preserved':True,'accepted_for_final':False},indent=2)+'\n');print('NOTCH_TRIAL_COMPLETE',sum(current.values()),sha(native),flush=True)
