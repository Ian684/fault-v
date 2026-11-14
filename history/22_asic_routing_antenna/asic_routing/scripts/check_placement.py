"""Check legal placement, PG connectivity and buffer-transparent circuit identity."""
from pathlib import Path
from collections import Counter,defaultdict
import json,re,os,hashlib
import odb
R=Path(__file__).resolve().parents[1]
tag=os.environ.get("PLACEMENT_RUN_TAG","placement_initial")
assert tag.replace("_","").isalnum()
run=R/"runs"/tag
out=R/"reports"/tag
out.mkdir(parents=True,exist_ok=True)
def load(p):
    d=odb.dbDatabase.create();odb.read_db(d,str(p));return d,d.getChip().getBlock()
db,b=load(next((run/"final/odb").glob("*.odb")))
ref,rb=load(R/"inputs/reference_floorplan.odb")
u=b.getDbUnitsPerMicron()
def box(o):return [o.xMin(),o.yMin(),o.xMax(),o.yMax()]
def inside(a,c):return a[0]>=c[0] and a[1]>=c[1] and a[2]<=c[2] and a[3]<=c[3]
# The Liberty is read only; timing tables are never edited.
libpath=Path("/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib")
s=libpath.read_text()
starts=list(re.finditer(r'\bcell\s*\("([^"]+)"\)\s*\{',s))
logic={}
for j,m in enumerate(starts):
    chunk=s[m.end():starts[j+1].start() if j+1<len(starts) else len(s)]
    pins=list(re.finditer(r'(?<![\w_])pin\s*\("([^"]+)"\)\s*\{',chunk))
    sig={}
    for k,p in enumerate(pins):
        body=chunk[p.end():pins[k+1].start() if k+1<len(pins) else len(chunk)]
        direction=re.search(r'\bdirection\s*:\s*"?(input|output|inout)"?',body)
        f=re.search(r'\bfunction\s*:\s*"([^"]+)"',body)
        if direction:sig[p[1]]=(direction[1],re.sub(r'\s+','',f[1]) if f else None)
    ff=tuple(re.findall(r'\b(clock(ed)?_on|next_state|clear|preset)\s*:\s*"([^"]+)"',chunk))
    logic[m[1]]=(sig,ff)
assert logic["sky130_fd_sc_hd__buf_1"][0]["X"][1].strip("()")=="A"
assert logic["sky130_fd_sc_hd__clkbuf_4"][0]["X"][1].strip("()")=="A"
def partition(block):
    parent={};phase={}
    def find(n):
        parent.setdefault(n,n);phase.setdefault(n,0)
        root=n;total=0
        while parent[root]!=root:
            total^=phase[root];root=parent[root]
        cursor=n;before=0
        while parent[cursor]!=cursor:
            nxt=parent[cursor];edge=phase[cursor]
            parent[cursor]=root;phase[cursor]=total^before
            before^=edge;cursor=nxt
        return root,total
    def union(a,c,flip=0):
        ra,pa=find(a);rc,pc=find(c)
        if ra==rc:
            assert pa^pc==flip,("Inconsistent signal polarity",a,c,flip)
        else:
            parent[ra]=rc;phase[ra]=pa^pc^flip
    union("test_a","test_b",1);union("test_b","test_c",1)
    assert find("test_a")[1]==find("test_c")[1]
    assert find("test_a")[1]!=find("test_b")[1]
    parent.clear();phase.clear()
    ends={};cells={};buffers=Counter();constants=0;dummy_count=0
    for i in block.getInsts():
        master=i.getMaster().getName()
        terms={t.getMTerm().getName():t for t in i.getITerms() if t.getMTerm().getSigType() not in ["POWER","GROUND"]}
        if not terms:continue
        def net(pin):
            t=terms[pin]
            return t.getNet().getName() if t.getNet() else "unconnected:"+i.getName()+"/"+pin
        sig,ff=logic.get(master,({},()))
        inputs=[p for p,v in sig.items() if v[0]=="input"]
        outputs={p:v[1] for p,v in sig.items() if v[0]=="output"}
        if i.getName().startswith("clkload") and not rb.findInst(i.getName()):
            assert outputs and not ff, (i.getName(),master)
            for pin in outputs:
                t=terms[pin];n=t.getNet()
                assert n is None or (not n.getBTerms() and all(x==t for x in n.getITerms())), ("Dummy drives logic",i.getName(),pin)
            dummy_count+=1
            continue
        if len(inputs)==1 and len(outputs)==1 and next(iter(outputs.values())).strip("()") in [inputs[0],"!"+inputs[0],inputs[0]+"'","~"+inputs[0]] and not ff:
            assert set(terms)==set(inputs)|set(outputs),(master,terms)
            union(net(inputs[0]),net(next(iter(outputs))),int(next(iter(outputs.values())).strip('()')!=inputs[0]))
            buffers[master]+=1
        elif outputs and not inputs and all(f.strip("()") in ["0","1"] for f in outputs.values()):
            constants+=1
            for p,f in outputs.items():union(net(p),"CONST:"+f.strip("()"))
        else:
            family=re.sub(r'_\d+$','',master) if master in logic else master
            cells[i.getName()]=(family,master)
            for pin in terms:ends[(i.getName(),family,pin)]=net(pin)
    for t in block.getBTerms():
        if t.getSigType() not in ["POWER","GROUND"]:
            ends[("TOP",t.getName())]=t.getNet().getName() if t.getNet() else "TOP_UNCONNECTED:"+t.getName()
    union("CONST:0","CONST:1",1)
    for value in ["0","1"]:ends[("CONST",value)]="CONST:"+value
    groups=defaultdict(set)
    for endpoint,net in ends.items():
        root,polarity=find(net);groups[root].add((endpoint,polarity))
    normalized=set()
    for values in groups.values():
        anchor=min(values,key=lambda x:repr(x[0]))[1]
        normalized.add(frozenset((key,polarity^anchor) for key,polarity in values))
    return normalized,cells,buffers,constants,len(ends),dummy_count
a,ca,ba,ka,ea,da=partition(rb)
z,cz,bz,kz,ez,dz=partition(b)
diff={"removed_components":[list(x) for x in list(a-z)[:8]],"added_components":[list(x) for x in list(z-a)[:8]],"removed_cells":sorted(set(ca)-set(cz))[:30],"added_cells":sorted(set(cz)-set(ca))[:30]}
(out/"connectivity_diff.json").write_text(json.dumps(diff,indent=2)+"\n")
assert a==z, ("Logical connectivity changed",len(a-z),len(z-a),out/"connectivity_diff.json")
assert set(ca)==set(cz)
negative_test=False
first_test=b.findInst("eco_sram_b0_first")
last_test=b.findInst("eco_sram_b0_last")
if first_test.getMaster().getName().startswith("sky130_fd_sc_hd__inv_"):
    original=last_test.findITerm("Y").getNet()
    targets=[t for t in original.getITerms() if t.getInst().getMaster().getType()=="BLOCK"]
    assert len(targets)==1
    target=targets[0]
    try:
        target.disconnect();target.connect(first_test.findITerm("Y").getNet())
        corrupted,*_=partition(b)
        assert corrupted!=a, "Checker missed a deliberately inverted SRAM address bit"
        negative_test=True
    finally:
        target.disconnect();target.connect(original)

resized=[]
for name,(family,master) in ca.items():
    assert cz[name][0]==family,name
    newmaster=cz[name][1]
    if master!=newmaster:
        assert master in logic and logic[master]==logic[newmaster],(name,master,newmaster)
        resized.append([name,master,newmaster])
rows=defaultdict(list)
for row in b.getRows():
    q=box(row.getBBox());rows[q[1]].append(q)
for y in rows:rows[y].sort()
height=2720
byrow=defaultdict(list)
macros={};std=[];pg=0;placement=Counter();clkbufs=[]
for i in b.getInsts():
    placement[i.getPlacementStatus()]+=1
    assert i.isPlaced(),(i.getName(),i.getPlacementStatus())
    q=box(i.getBBox())
    assert inside(q,box(b.getCoreArea())),(i.getName(),q)
    for t in i.getITerms():
        st=t.getMTerm().getSigType()
        if st in ["POWER","GROUND"]:
            assert t.getNet() and t.getNet().getName()==("VPWR" if st=="POWER" else "VGND"),(i.getName(),t.getMTerm().getName())
            pg+=1
    if i.getMaster().getType()=="BLOCK":
        base=rb.findInst(i.getName())
        assert base and i.isFixed() and q==box(base.getBBox()) and i.getOrient()==base.getOrient(),i.getName()
        macros[i.getName()]={"bbox":[v/u for v in q],"orientation":str(i.getOrient())}
    else:
        assert (q[3]-q[1])%height==0,(i.getName(),q)
        for y in range(q[1],q[3],height):
            assert any(q[0]>=r[0] and q[2]<=r[2] for r in rows[y]),(i.getName(),q,y)
            byrow[y].append((q[0],q[2],i.getName()))
        std.append([q[0]/u,q[1]/u,q[2]/u,q[3]/u,i.getMaster().getName()])
        if i.getName().startswith(("clkbuf","delaybuf","clknet")) or "clkbuf_" in i.getMaster().getName():
            clkbufs.append([i.getName(),[v/u for v in q],i.getMaster().getName()])
for y,items in byrow.items():
    items.sort()
    for x,c in zip(items,items[1:]):
        assert x[1]<=c[0],("Cell overlap",y,x,c)
assert len(macros)==18
ports={t.getName():[(p.getPlacementStatus(),[box(q) for q in p.getBoxes()]) for p in t.getBPins()] for t in b.getBTerms() if t.getSigType() not in ["POWER","GROUND"]}
oldports={t.getName():[(p.getPlacementStatus(),[box(q) for q in p.getBoxes()]) for p in t.getBPins()] for t in rb.getBTerms() if t.getSigType() not in ["POWER","GROUND"]}
assert ports==oldports and len(ports)==108
def power_shapes(block):
    result={}
    for name in ["VPWR","VGND"]:
        net=block.findNet(name)
        assert net and net.getSWires()
        shapes=[]
        for wire in net.getSWires():
            for q in wire.getWires():
                kind=(q.getTechVia() or q.getBlockVia()).getName() if q.isVia() else q.getTechLayer().getName()
                shapes.append((q.isVia(),kind,q.xMin(),q.yMin(),q.xMax(),q.yMax()))
        assert shapes
        result[name]=sorted(shapes)
    return result
assert power_shapes(rb)==power_shapes(b), "PDN geometry changed"
clock_group=next(group for group in a if any(endpoint==("TOP","clk") for endpoint,polarity in group))
assert len(clock_group)-1==2961
unused_drivers=[]
for i in b.getInsts():
    for t in i.getITerms():
        if t.getIoType()!="OUTPUT": continue
        net=t.getNet()
        active=net and (any(p.getIoType() in ["OUTPUT","INOUT"] for p in net.getBTerms()) or any(p.getIoType() in ["INPUT","INOUT"] for p in net.getITerms()))
        if not active:unused_drivers.append((i.getName()+"/"+t.getMTerm().getName()).replace(chr(92),""))
clock_edges=[];clock_levels=[];clock_tree_cells={};seen=set()
queue=[(b.findBTerm("clk").getNet(),0)]
while queue:
    net,depth=queue.pop()
    assert net.getName() not in seen, ("Clock reconverges",net.getName())
    seen.add(net.getName())
    drivers=[p for p in net.getITerms() if p.getIoType()=="OUTPUT"]
    if drivers:
        assert len(drivers)==1
        ok,sx,sy=drivers[0].getAvgXY();assert ok
    else:
        pins=[p for p in net.getBTerms() if p.getIoType()=="INPUT"]
        assert len(pins)==1
        q=next(iter(next(iter(pins[0].getBPins())).getBoxes()))
        sx=(q.xMin()+q.xMax())/2;sy=(q.yMin()+q.yMax())/2
    for t in net.getITerms():
        if t.getIoType()!="INPUT": continue
        ok,tx,ty=t.getAvgXY();assert ok
        clock_edges.append([sx/u,sy/u,tx/u,ty/u])
        inst=t.getInst();master=inst.getMaster().getName()
        if (master.startswith("sky130_fd_sc_hd__df") and t.getMTerm().getName()=="CLK") or (inst.getMaster().getType()=="BLOCK" and t.getMTerm().getName() in ["clk0","clk1"]):
            clock_levels.append(depth)
        sig,ff=logic.get(master,({},()))
        ins=[p for p,v in sig.items() if v[0]=="input"]
        outs={p:v[1] for p,v in sig.items() if v[0]=="output"}
        if len(ins)==1 and len(outs)==1 and next(iter(outs.values())).strip("()")==ins[0] and not ff:
            nextnet=inst.findITerm(next(iter(outs))).getNet()
            if nextnet and any(p.getIoType()=="INPUT" for p in nextnet.getITerms()):
                clock_tree_cells[inst.getName()]=master
                queue.append((nextnet,depth+1))
assert len(clock_levels)==2961
ff_count=sum(i.getMaster().getName().startswith("sky130_fd_sc_hd__df") for i in b.getInsts())
assert ff_count==2925
summary={"flip_flops":ff_count,"active_clock_buffer_count":len(clock_tree_cells),"negative_inversion_fault_detected":negative_test,"clock_connectivity_edges":clock_edges,"active_clock_buffer_cells":clock_tree_cells,"clock_buffer_depth_range":[min(clock_levels),max(clock_levels)],"unused_output_driver_pins":sorted(unused_drivers),"clock_sink_pins":2961,"pdn_geometry_unchanged":True,"pass":True,"run":tag,"instances":len(b.getInsts()),"placement_status":dict(placement),"fixed_macros":18,"signal_pins":108,"connected_pg_iterms":pg,"base_unary_buffer_inverter_cells":sum(ba.values()),"final_unary_buffer_inverter_cells":sum(bz.values()),"verified_unused_cts_dummy_loads":dz,"base_constant_cells":ka,"final_constant_cells":kz,"nonbuffer_instances":len(ca),"nonbuffer_endpoints":ea,"connected_components":len(a),"resized_nonbuffer_cells":len(resized),"clock_named_or_clock_master_instances":len(clkbufs),"stdcell_area_um2":sum((q[2]-q[0])*(q[3]-q[1]) for q in std),"macro_area_um2":sum((m["bbox"][2]-m["bbox"][0])*(m["bbox"][3]-m["bbox"][1]) for m in macros.values()),"netlist_sha256":hashlib.sha256(next((run/"final/nl").glob("*.v")).read_bytes()).hexdigest(),"proof_scope":"Exact signal connectivity with verified BUF/INV functions and relative-polarity union-find, with constants canonicalized; drive variants require identical Liberty signal/FF signatures. New CTS clkload cells must be combinational with no connected output load and are excluded from functional endpoints. Not RTL formal equivalence.","macros":macros,"clock_buffers":clkbufs,"standard_cells":std}
(out/"placement_checks.json").write_text(json.dumps(summary,indent=2)+"\n")
(out/"resized_cells.json").write_text(json.dumps(resized,indent=2)+"\n")
print("ALL PLACEMENT LEGALITY / POWER CONNECTION / POLARITY-AWARE CONNECTIVITY CHECKS PASSED")
print(json.dumps({k:v for k,v in summary.items() if k not in ["macros","clock_buffers","standard_cells","unused_output_driver_pins","clock_connectivity_edges","active_clock_buffer_cells"]},indent=2))
