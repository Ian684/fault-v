"""Check actual copper/via/pin connected components on every routed signal net."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path(sys.argv[1]);report=C/sys.argv[2]
db,b=load(source);tech=db.getTech();metal={'li1','met1','met2','met3','met4','met5'}
text=(R/'scripts/check_antenna_signal_connectivity.py').read_text();tree=ast.parse(text);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='connectivity')
code=ast.get_source_segment(text,node)
needle='sum(diode for name,diode,i in terminals))';assert code.count(needle)==1
code=code.replace(needle,'sum(diode for name,diode,i in terminals),len({root(i) for i in range(len(shapes))}))')
exec(compile(code,'existing_connectivity_with_all_copper_components','exec'))
checked=0;bad=[];missing_wires=[];nontrivial=0;diodes=0
for net in b.getNets():
    if str(net.getSigType()) in ('POWER','GROUND'):continue
    pins=[p for p in net.getITerms() if str(p.getMTerm().getSigType()) not in ('POWER','GROUND')]
    if len(pins)+len(net.getBTerms())<2:continue
    checked+=1
    if not net.getWire():missing_wires.append(net.getName());continue
    missing,disconnected,count,components=connectivity(net);diodes+=count
    if missing or disconnected or components!=1:bad.append({'net':net.getName(),'unconnected_diodes':missing,'original_terminals_disconnected':disconnected,'all_copper_pin_components':components})
    if checked%5000==0:print('SIGNAL_CONNECTIVITY_PROGRESS',checked,'bad',len(bad),flush=True)
with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
record={'source_sha256':digest,'checked_multi_terminal_signal_clock_nets':checked,'diode_terminals':diodes,'missing_wires':missing_wires,'bad_nets':bad,'all_signal_geometry_connected':not missing_wires and not bad,'scope':'Actual S/R/via and transformed terminal geometry; requires all signal wire shapes and pins to belong to one component on every multi-terminal SIGNAL/CLOCK net. Independent full LVS is still required.'}
assert checked>40000
report.write_text(json.dumps(record,indent=2)+'\n');print('SIGNAL_CONNECTIVITY_COMPLETE',checked,'bad',len(bad),'missing',len(missing_wires),flush=True)
