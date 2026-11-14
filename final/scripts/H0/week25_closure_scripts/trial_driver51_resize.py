"""Check one real max-RC buffer-limit failure using a Boolean-equivalent native master."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');R=C.parent/'routing';source=Path('/runtime/signal_closed.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
selected=json.loads((C/'reports/signal_selection.json').read_text());assert sha(source)==selected['source_sha256'] and selected['independent_DRC']==0
lib=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib';text=lib.read_text()
tree=ast.parse((R/'scripts/prepare_antenna_drive.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='logic');exec(compile(ast.Module(body=[node],type_ignores=[]),'reviewed_liberty_contract','exec'))
old='sky130_fd_sc_hd__buf_1';new='sky130_fd_sc_hd__buf_2';name='_30389_';assert logic(old)==logic(new) and logic(old)!=logic('sky130_fd_sc_hd__inv_1')
t=Tech();t.readLiberty(str(lib));t.readLiberty(str(R/'macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib'))
design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock();tech=db.getTech()
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b);inst=b.findInst(name);assert inst.getMaster().getName()==old
position=tuple(inst.getLocation());orient=str(inst.getOrient());status=str(inst.getPlacementStatus());oldbox=inst.getBBox();old_box=[oldbox.xMin(),oldbox.yMin(),oldbox.xMax(),oldbox.yMax()]
pin_geometry=lambda i:{p.getMTerm().getName():[(l.getName(),[q.xMin(),q.yMin(),q.xMax(),q.yMax()]) for l,q in p.getGeometries()] for p in i.getITerms()}
oldpins=pin_geometry(inst);assert inst.swapMaster(db.findMaster(new));inst.setOrient(orient);inst.setLocation(*position);inst.setPlacementStatus(status)
assert before[1:]==fixed(b)[1:]
expected=dict(before[0]);expected[name]=(new,*before[0][name][1:]);assert fixed(b)[0]==expected
assert wires(b)==oldw and guides(b)==oldg and obstructions(b)==oldo
answer=str(design.evalTclString('set e [catch {check_placement -verbose} msg]; list $e $msg'));placement=answer.startswith('0 ')
metal={'li1','met1','met2','met3','met4','met5'}
tree=ast.parse((R/'scripts/check_antenna_signal_connectivity.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='connectivity');exec(compile(ast.Module(body=[node],type_ignores=[]),'actual_target_contact_check','exec'))
affected={p.getNet().getName() for p in inst.getITerms() if p.getNet() and str(p.getSigType()) not in ('POWER','GROUND')};assert affected=={'net3347','_03595_'}
contacts={n:connectivity(b.findNet(n)) for n in sorted(affected)}
peer=None;x,y=position
if placement and all(not m and not d for m,d,c in contacts.values()):
    for i in b.getInsts():
        if i.getName()==name or i.getMaster().getName()!=new or str(i.getOrient())!=orient:continue
        px,py=i.getLocation()
        if (x-px)%460 or (y-py)%340:continue
        if all(str(p.getSigType()) in ('POWER','GROUND') or i.findITerm(p.getMTerm().getName()).getPrefAccessPoints() and all(any(l.getName()==a.getLayer().getName() and q.xMin()<=x+a.getPoint()[0]<=q.xMax() and q.yMin()<=y+a.getPoint()[1]<=q.yMax() for l,q in p.getGeometries()) for a in i.findITerm(p.getMTerm().getName()).getPrefAccessPoints()) for p in inst.getITerms()):peer=i;break
    assert peer,'No valid native buf_2 access peer'
    inst.setPinAccessIdx(peer.getPinAccessIdx())
    for pin in inst.getITerms():
        pin.clearPrefAccessPoints()
        for a in peer.findITerm(pin.getMTerm().getName()).getPrefAccessPoints():pin.setAccessPoint(a.getMPin(),a)
record={'source_sha256':sha(source),'cell':name,'old_master':old,'new_master':new,'position':position,'orientation':orient,'old_bbox':old_box,'new_bbox':[inst.getBBox().xMin(),inst.getBBox().yMin(),inst.getBBox().xMax(),inst.getBBox().yMax()],'Boolean_and_signal_pin_contract_equal':True,'Liberty_sha256':sha(lib),'placement_pass':placement,'placement_response':answer,'old_pin_geometry':oldpins,'new_pin_geometry':pin_geometry(inst),'affected_nets':sorted(affected),'target_net_contacts':contacts,'all_other_cells_graph_PG_wire_bytes_guides_obstructions_preserved':True,'native_access_peer':peer.getName() if peer else None,'accepted_for_final':False}
if peer:
    native=Path('/runtime_final/driver51_a.odb');dest=C/'inputs/driver51_a.odb';assert not native.exists() and not dest.exists();odb.write_db(db,str(native))
    with native.open('rb') as inp,dest.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
    assert sha(native)==sha(dest);record['output_sha256']=sha(native)
(C/'reports/driver51_trial.json').write_text(json.dumps(record,indent=2)+'\n');print('ONE_DRIVER_TRIAL',placement,contacts,record.get('output_sha256'),flush=True)
