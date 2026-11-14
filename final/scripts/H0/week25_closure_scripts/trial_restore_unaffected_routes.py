"""Keep ECO-near routes while restoring the complete original background routing."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives,path_type
C=Path('/work/week25_closure');R=C.parent/'routing'
source=Path('/route_b/1-openroad-detailedrouting/native_final.odb');reference=Path('/runtime/F.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==json.loads((C/'reports/short_b_final_independent.json').read_text())['odb_sha256']
assert sha(reference)=='fe627dd4b1ff4c152dcfa9dd5d08b05c13b7272ab4065d7f0cb8af3d87dd1380'
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();rd,rb=load(reference)
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b)
drivers=set(json.loads((C/'reports/cached_input.json').read_text())['equivalent_drivers']);assert len(drivers)==50
regions=[]
for name in drivers:
    for block in (b,rb):
        z=block.findInst(name).getBBox();regions.append((z.xMin()-2000,z.yMin()-2000,z.xMax()+2000,z.yMax()+2000))
def hit(q):return any(q[0]<=z and q[2]>=a and q[1]<=f and q[3]>=c for a,c,z,f in regions)
def box(q,tech,block):
    if q[0]=='S':
        h=tech.findLayer(q[1]).getWidth()//2;_,l,x1,y1,x2,y2,e1,e2=q
        return (x1-h,y1-e1,x2+h,y2+e2) if x1==x2 else (x1-e1,y1-h,x2+e2,y2+h)
    if q[0]=='R':return q[2:6]
    v=tech.findVia(q[1]) if q[0]=='T' else block.findVia(q[1]);z=v.getBBox();x,y=q[2:];return (z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y)
out=C/'reports/background_restore_a';out.mkdir(exist_ok=False)
restored=[];retained=[];identical=0
for net in b.getNets():
    w=net.getWire()
    if not w:continue
    name=net.getName();old=rb.findNet(name);assert old and old.getWire()
    terms=lambda n:sorted((p.getInst().getName(),p.getMTerm().getName()) for p in n.getITerms())
    assert terms(net)==terms(old)
    orig=primitives(old.getWire())[0];now=primitives(w)[0]
    if orig==now:identical+=1;continue
    touches=bool({i for i,p in terms(net)}&drivers) or any(hit(box(q,rd.getTech(),rb)) for q in orig) or any(hit(box(q,db.getTech(),b)) for q in now)
    if touches:retained.append(name);continue
    odb.dbWire.destroy(w);w=odb.dbWire.create(net);w.append(old.getWire())
    assert primitives(w)[0]==orig and path_type(w)=='ROUTED';restored.append(name)
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo
assert {n:v for n,v in wires(b).items() if n not in restored}=={n:v for n,v in oldw.items() if n not in restored}
native=Path('/runtime_final/background_restore_a.odb');permanent=C/'inputs/background_restore_a.odb';assert not native.exists() and not permanent.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,permanent.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(permanent)
result={'source_sha256':sha(source),'reference_sha256':sha(reference),'output_sha256':sha(native),'identical_routes':identical,'restored_original_routes':restored,'retained_ECO_near_routes':retained,'all_cells_graph_PG_guides_obstructions_and_other_wire_bytes_preserved':True,'accepted':False}
(out/'input.json').write_text(json.dumps(result,indent=2)+'\n');print('BACKGROUND_RESTORE',len(restored),len(retained),identical,flush=True)
design.evalTclString('set_thread_count 2');design.evalTclString(f'drt::check_drc -output_file {out}/raw.rpt -marker_name BackgroundRestoreTrial')
text=(out/'raw.rpt').read_text();rows=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = ([^\n]+)',text);assert len(rows)==text.count('violation type:')
result['raw_markers']=len(rows);result['raw_categories']=dict(Counter(r[0] for r in rows));(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print('BACKGROUND_RESTORE_RAW',len(rows),result['raw_categories'],flush=True)
