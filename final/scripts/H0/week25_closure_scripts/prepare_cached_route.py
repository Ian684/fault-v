"""Preserve original native APs; rebuild all low-metal routes around the resized cells."""
from pathlib import Path
from collections import Counter,defaultdict
from openroad import Tech,Design
import ast,hashlib,json,re,struct,odb
C=Path('/work/week25_closure');R=Path('/work/routing')
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','guides','guide_sig','obstructions'}),('search_manual_eco.py',{'primitives'})]:
    tree=ast.parse((R/'scripts'/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
lib=Path('/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib');text=lib.read_text()
tree=ast.parse((R/'scripts/prepare_antenna_drive.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='logic');exec(compile(ast.Module(body=[node],type_ignores=[]),'logic','exec'))
source=C/'inputs/minimal_partial.odb';initial=json.loads((C/'reports/minimal_input.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==initial['partial_sha256']
t=Tech();t.readLiberty(str(lib));t.readLiberty('/work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib')
design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock()
before=fixed(b);old_wires=wires(b);obs=obstructions(b)
names=set(initial['resized'])|{'_39335_','_37262_'};assert len(names)==50
def preferences(exclude):
    return {(i.getName(),p.getMTerm().getName()):(i.getPinAccessIdx(),tuple(sorted((a.getLayer().getName(),tuple(a.getPoint())) for a in p.getPrefAccessPoints()))) for i in b.getInsts() if i.getName() not in exclude for p in i.getITerms()}
old_prefs=preferences(names)
for name,old,new in [('_39335_','sky130_fd_sc_hd__buf_1','sky130_fd_sc_hd__buf_2'),('_37262_','sky130_fd_sc_hd__clkbuf_2','sky130_fd_sc_hd__clkbuf_4')]:
    inst=b.findInst(name);assert inst and inst.getMaster().getName()==old and logic(old)==logic(new)
    assert inst.swapMaster(db.findMaster(new))
statuses={i.getName():str(i.getPlacementStatus()) for i in b.getInsts()}
for inst in b.getInsts():
    if inst.getName() not in ('_39335_','_37262_'):inst.setPlacementStatus('FIRM')
answer=str(design.evalTclString('set e [catch {detailed_placement -max_displacement {50 50}; check_placement -verbose} m]; list $e $m'))
assert answer.startswith('0 '),answer
for inst in b.getInsts():inst.setPlacementStatus(statuses[inst.getName()])
after=fixed(b)
assert {n for n in before[0] if before[0][n]!=after[0][n]}=={'_39335_','_37262_'}
assert before[1:]==after[1:] and obstructions(b)==obs and wires(b)==old_wires
peers=defaultdict(list)
for inst in b.getInsts():
    if inst.getName() not in names:peers[(inst.getMaster().getName(),str(inst.getOrient()))].append(inst)
native_access={}
for name in sorted(names):
    inst=b.findInst(name);x,y=inst.getLocation();chosen=None
    for peer in peers[(inst.getMaster().getName(),str(inst.getOrient()))]:
        px,py=peer.getLocation()
        if (x-px)%460 or (y-py)%340:continue
        valid=True
        for pin in inst.getITerms():
            if str(pin.getMTerm().getSigType()) in ('POWER','GROUND'):continue
            points=peer.findITerm(pin.getMTerm().getName()).getPrefAccessPoints()
            if not points:valid=False;break
            if any(not any(l.getName()==a.getLayer().getName() and z.xMin()<=x+a.getPoint()[0]<=z.xMax() and z.yMin()<=y+a.getPoint()[1]<=z.yMax() for l,z in pin.getGeometries()) for a in points):valid=False;break
        if valid:chosen=peer;break
    assert chosen is not None,('No valid native peer',name)
    inst.setPinAccessIdx(chosen.getPinAccessIdx())
    for pin in inst.getITerms():
        pin.clearPrefAccessPoints()
        peerpin=chosen.findITerm(pin.getMTerm().getName())
        for point in peerpin.getPrefAccessPoints():pin.setAccessPoint(point.getMPin(),point)
        assert tuple(sorted((a.getLayer().getName(),tuple(a.getPoint())) for a in pin.getPrefAccessPoints()))==tuple(sorted((a.getLayer().getName(),tuple(a.getPoint())) for a in peerpin.getPrefAccessPoints()))
    native_access[name]={'peer':chosen.getName(),'master':inst.getMaster().getName(),'orientation':str(inst.getOrient()),'pin_access_index':inst.getPinAccessIdx(),'location':list(inst.getLocation())}
assert preferences(names)==old_prefs,'Unrelated native pin preferences changed'
rois=[]
for name in names:
    box=b.findInst(name).getBBox();rois.append((box.xMin()-2000,box.yMin()-2000,box.xMax()+2000,box.yMax()+2000))
bins=defaultdict(set);pitch=50000
for i,(x0,y0,x1,y1) in enumerate(rois):
    for gx in range(x0//pitch,x1//pitch+1):
        for gy in range(y0//pitch,y1//pitch+1):bins[gx,gy].add(i)
def intersects(box):
    x0,y0,x1,y1=box
    for gx in range(x0//pitch,x1//pitch+1):
        for gy in range(y0//pitch,y1//pitch+1):
            for i in bins.get((gx,gy),()):
                a,c,z,f=rois[i]
                if x0<=z and x1>=a and y0<=f and y1>=c:return True
    return False
assert intersects(rois[0]) and not intersects((-1000000,-1000000,-900000,-900000))
dirty=set(initial['cleared_nets'])
for name in names:
    dirty.update(p.getNet().getName() for p in b.findInst(name).getITerms() if p.getNet() and str(p.getMTerm().getSigType()) not in ('POWER','GROUND'))
for net in b.getNets():
    wire=net.getWire()
    if wire is None or net.getName() in dirty or str(net.getSigType()) in ('POWER','GROUND'):continue
    geometry,_=primitives(wire)
    for item in geometry:
        if item[0]=='S' and item[1] in ('li1','met1','met2'):
            _,layer,x0,y0,x1,y1,*_=item;hit=intersects((min(x0,x1)-500,min(y0,y1)-500,max(x0,x1)+500,max(y0,y1)+500))
        elif item[0] in ('T','V'):
            _,via,x,y=item;hit=intersects((x-500,y-500,x+500,y+500))
        elif item[0]=='R' and item[1] in ('li1','met1','met2'):hit=intersects(tuple(item[2:]))
        else:hit=False
        if hit:dirty.add(net.getName());break
for name in dirty:
    net=b.findNet(name);assert net is not None
    if net.getWire():odb.dbWire.destroy(net.getWire())
retained={n:d for n,d in old_wires.items() if n not in dirty}
assert wires(b)==retained and fixed(b)==after and preferences(names)==old_prefs
partial=C/'inputs/cached_partial.odb';global_input=C/'inputs/cached_global.odb'
assert not partial.exists() and not global_input.exists();odb.write_db(db,str(partial))
for net in b.getNets():
    if net.getWire():odb.dbWire.destroy(net.getWire())
odb.write_db(db,str(global_input))
state=json.loads((C/'global_state.json').read_text());state.update(odb=str(global_input),metrics={})
(C/'cached_global_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_global.json').read_text());cfg['KLAYOUT_CONFLICT_RESOLUTION']='OverwriteCell';cfg['MACROS']['sky130_sram_2kbyte_1rw1r_32x512_8']['gds']=['/work/week25_closure/macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim.gds']
(C/'config_cached_global.json').write_text(json.dumps(cfg,indent=2)+'\n')
proof={'accepted':False,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'partial_sha256':hashlib.sha256(partial.read_bytes()).hexdigest(),'global_sha256':hashlib.sha256(global_input.read_bytes()).hexdigest(),'equivalent_drivers':native_access,'all_other_native_preferences_preserved':True,'only_two_additional_driver_changes':True,'cleared_nets':sorted(dirty),'retained_wire_sha256':retained,'retained_routes':len(retained),'neighborhood_halo_um':2,'scope':'50 equivalent drive changes; native same-master/orientation/site-phase access points copied from unchanged peers, no invented AP coordinates. All unrelated cells, graph, PG and cached preferences retained; all low-metal/via routes touching enlarged cells cleared.'}
(C/'reports/cached_input.json').write_text(json.dumps(proof,indent=2)+'\n')
print('CACHED_ACCESS_INPUT',len(names),'drivers',len(dirty),'dirty nets',len(retained),'exact routes retained',flush=True)
