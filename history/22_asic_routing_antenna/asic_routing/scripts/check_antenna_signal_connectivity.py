"""Check actual metal/via/pin connected components on every diode-bearing net."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,os,odb
R=Path('/work/routing');tag=os.environ['PLACEMENT_RUN_TAG'];assert tag.replace('_','').isalnum()
path=Path(os.environ.get('ANTENNA_CONNECTIVITY_ODB',str(R/'runs'/tag/'final/odb/fault_v_asic_top.odb')))
db=odb.dbDatabase.create();odb.read_db(db,str(path));b=db.getChip().getBlock();tech=db.getTech()
tree=ast.parse((R/'scripts/search_manual_eco.py').read_text(encoding='utf-8-sig'))
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='primitives'];assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),'primitives','exec'))
metal={'li1','met1','met2','met3','met4','met5'}
def connectivity(net):
    shapes=[];wire=net.getWire();assert wire,net.getName()
    primitives_by_count,_=primitives(wire)
    for q in primitives_by_count.elements():
        if q[0]=='S':
            _,layer,x1,y1,x2,y2,e1,e2=q;half=tech.findLayer(layer).getWidth()//2
            box=(x1-half,y1-e1,x2+half,y2+e2) if x1==x2 else (x1-e1,y1-half,x2+e2,y2+half)
            shapes.append([(layer,box)])
        elif q[0]=='R':shapes.append([(q[1],tuple(q[2:6]))])
        elif q[0] in ['T','V']:
            _,name,x,y=q;via=tech.findVia(name) if q[0]=='T' else b.findVia(name);assert via
            shapes.append([(box.getTechLayer().getName(),(box.xMin()+x,box.yMin()+y,box.xMax()+x,box.yMax()+y)) for box in via.getBoxes() if box.getTechLayer().getName() in metal])
        else:raise AssertionError(q)
    terminals=[]
    for term in net.getITerms():
        if str(term.getMTerm().getSigType()) in ['POWER','GROUND']:continue
        boxes=[(layer.getName(),(box.xMin(),box.yMin(),box.xMax(),box.yMax())) for layer,box in term.getGeometries() if layer.getName() in metal]
        assert boxes;terminals.append((term.getInst().getName()+'/'+term.getMTerm().getName(),term.getInst().getMaster().getName()=='sky130_fd_sc_hd__diode_2',len(shapes)));shapes.append(boxes)
    for term in net.getBTerms():
        if str(term.getSigType()) in ['POWER','GROUND']:continue
        boxes=[(box.getTechLayer().getName(),(box.xMin(),box.yMin(),box.xMax(),box.yMax())) for pin in term.getBPins() for box in pin.getBoxes() if box.getTechLayer().getName() in metal]
        assert boxes;terminals.append(('TOP/'+term.getName(),False,len(shapes)));shapes.append(boxes)
    parent=list(range(len(shapes)))
    def root(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    grouped=defaultdict(list)
    for i,boxes in enumerate(shapes):
        for layer,box in boxes:grouped[layer].append((i,box))
    for values in grouped.values():
        values.sort(key=lambda q:q[1][0])
        for a,(i,z) in enumerate(values):
            for k in range(a+1,len(values)):
                j,w=values[k]
                if w[0]>z[2]:break
                if z[0]<=w[2] and z[1]<=w[3] and z[3]>=w[1]:
                    ri,rj=root(i),root(j)
                    if ri!=rj:parent[ri]=rj
    old=[root(i) for name,diode,i in terminals if not diode];assert old
    return ([name for name,diode,i in terminals if diode and root(i)!=old[0]],len(set(old))!=1,sum(diode for name,diode,i in terminals))
checked=0;diodes=0;bad=[];bad_old=[]
for net in b.getNets():
    if str(net.getSigType()) in ['POWER','GROUND']:continue
    if not any(t.getInst().getMaster().getName()=='sky130_fd_sc_hd__diode_2' for t in net.getITerms()):continue
    missing,old_bad,count=connectivity(net);checked+=1;diodes+=count
    bad.extend((net.getName(),name) for name in missing)
    if old_bad:bad_old.append(net.getName())
assert checked>0 and diodes>=7251
out=R/'reports'/tag;out.mkdir(parents=True,exist_ok=True)
record={'pass':not bad and not bad_old,'run':tag,'source_odb_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'checked_diode_nets':checked,'diode_terminals':diodes,'unconnected_diode_terminals':len(bad),'first_unconnected_diodes':bad[:20],'nets_with_disconnected_original_terminals':bad_old,'scope':'Geometric connected components from actual routed S/R/via metal and transformed ITerm/BTerm shapes. Every added diode and all original signal terminals of each diode-bearing net must join one component. Not transistor-level foundry LVS.'}
report=Path(os.environ.get('ANTENNA_CONNECTIVITY_REPORT',str(out/'antenna_signal_connectivity.json')))
report.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
assert record['pass'], 'Unconnected antenna diode or original signal terminal'
