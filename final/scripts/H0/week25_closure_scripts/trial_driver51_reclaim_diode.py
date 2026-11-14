"""Fit the one required larger buffer by reclaiming an obstructing passive antenna diode."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import fixed,wires,guides,obstructions,primitives,encode_fixed,path_type
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/runtime/signal_closed.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==json.loads((C/'reports/signal_selection.json').read_text())['source_sha256']
lib=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib';text=lib.read_text()
tree=ast.parse((R/'scripts/prepare_antenna_drive.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='logic');exec(compile(ast.Module(body=[node],type_ignores=[]),'reviewed_liberty_contract','exec'))
old='sky130_fd_sc_hd__buf_1';new='sky130_fd_sc_hd__buf_2';name='_30389_';removed_name='ANTENNA_7502';assert logic(old)==logic(new) and logic(old)!=logic('sky130_fd_sc_hd__inv_1')
t=Tech();t.readLiberty(str(lib));t.readLiberty(str(R/'macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib'));design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b);inst=b.findInst(name);assert inst.getMaster().getName()==old
position=tuple(inst.getLocation());orient=str(inst.getOrient());status=str(inst.getPlacementStatus())
diode=b.findInst(removed_name);assert diode and diode.getMaster().getName()=='sky130_fd_sc_hd__diode_2' and diode.findITerm('DIODE').getNet().getName()=='net3212'
diode_record={'name':removed_name,'master':diode.getMaster().getName(),'position':list(diode.getLocation()),'orientation':str(diode.getOrient()),'signal_net':'net3212','reason':'Passive antenna diode overlaps the required larger buffer; actual antenna checks and later insertion must repair any resulting antenna violation.'}
assert inst.swapMaster(db.findMaster(new));inst.setOrient(orient);inst.setLocation(*position);inst.setPlacementStatus(status)
# Remove this passive diode's obsolete LI1/mcon contact before reclaiming its site.
n=b.findNet('net3212');wire=n.getWire();original=primitives(wire)[0];box=diode.getBBox();removed_copper=Counter()
for q,count in original.items():
    if q[0] in ('T','V'):
        via=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1])
        if via.getBottomLayer().getName()=='li1' and via.getTopLayer().getName()=='met1' and box.xMin()<=q[2]<=box.xMax() and box.yMin()<=q[3]<=box.yMax():removed_copper[q]=count
    elif q[0] in ('S','R') and q[1]=='li1':
        a,c,z,f=q[2:6]
        if box.xMin()<=a<=z<=box.xMax() and box.yMin()<=c<=f<=box.yMax():removed_copper[q]=count
assert removed_copper,'Missing actual diode contact geometry'
remaining=original-removed_copper;encode_fixed(wire,remaining,tech,b)
tree=ast.parse((R/'scripts/search_manual_eco.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='normalize_routes');exec(compile(ast.Module(body=[node],type_ignores=[]),'reviewed_wire_normalization','exec'));normalize_routes(wire)
assert primitives(wire)[0]==remaining and path_type(wire)=='ROUTED'
odb.dbInst_destroy(diode)
expected=dict(before[0]);expected.pop(removed_name);expected[name]=(new,*before[0][name][1:])
graph={k:(v[0],tuple(p for p in v[1] if p[0]!=removed_name),v[2]) for k,v in before[1].items()}
assert fixed(b)==(expected,graph,before[2]) and obstructions(b)==oldo and guides(b)==oldg
assert {k:v for k,v in wires(b).items() if k!='net3212'}=={k:v for k,v in oldw.items() if k!='net3212'} and primitives(n.getWire())[0]==remaining
answer=str(design.evalTclString('set e [catch {check_placement -verbose} msg]; list $e $msg'));placement=answer.startswith('0 ')
metal={'li1','met1','met2','met3','met4','met5'}
tree=ast.parse((R/'scripts/check_antenna_signal_connectivity.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='connectivity');exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_target_contact_check','exec'))
affected={'net3347','_03595_','net3212'};contacts={k:connectivity(b.findNet(k)) for k in sorted(affected)};peer=None;x,y=position
if placement and all(not m and not d for m,d,c in contacts.values()):
    for i in b.getInsts():
        if i.getName()==name or i.getMaster().getName()!=new or str(i.getOrient())!=orient:continue
        px,py=i.getLocation()
        if (x-px)%460 or (y-py)%340:continue
        if all(str(p.getSigType()) in ('POWER','GROUND') or i.findITerm(p.getMTerm().getName()).getPrefAccessPoints() and all(any(l.getName()==a.getLayer().getName() and q.xMin()<=x+a.getPoint()[0]<=q.xMax() and q.yMin()<=y+a.getPoint()[1]<=q.yMax() for l,q in p.getGeometries()) for a in i.findITerm(p.getMTerm().getName()).getPrefAccessPoints()) for p in inst.getITerms()):peer=i;break
    assert peer,'No valid native buf_2 access peer';inst.setPinAccessIdx(peer.getPinAccessIdx())
    for pin in inst.getITerms():
        pin.clearPrefAccessPoints()
        for a in peer.findITerm(pin.getMTerm().getName()).getPrefAccessPoints():pin.setAccessPoint(a.getMPin(),a)
record={'source_sha256':sha(source),'cell':name,'old_master':old,'new_master':new,'position':position,'orientation':orient,'Boolean_and_signal_pin_contract_equal':True,'Liberty_sha256':sha(lib),'placement_pass':placement,'placement_response':answer,'removed_passive_diodes':[diode_record],'removed_passive_diode_branch_copper':list(removed_copper.elements()),'target_net_contacts':contacts,'native_access_peer':peer.getName() if peer else None,'all_other_cells_and_PG_unchanged':True,'all_other_signal_copper_geometry_unchanged':True,'only_reserialized_signal_net':'net3212','all_other_wire_bytes_guides_obstructions_preserved':True,'accepted_for_final':False}
if peer:
    antenna=int(str(design.evalTclString('check_antennas -report_file /work/week25_closure/reports/driver51_b_antenna.rpt')));record['antenna_nets']=antenna
    native=Path('/runtime_final/driver51_b.odb');dest=C/'inputs/driver51_b.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
    with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
    assert sha(native)==sha(dest);record['output_sha256']=sha(native)
(C/'reports/driver51_trial_b.json').write_text(json.dumps(record,indent=2)+'\n');print('ONE_DRIVER_DIODE_RECLAIM_TRIAL',placement,contacts,record.get('output_sha256'),flush=True)
