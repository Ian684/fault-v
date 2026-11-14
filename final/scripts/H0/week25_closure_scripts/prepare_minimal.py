"""Repair measured drivers only, preserving every unrelated cell and native wire."""
from pathlib import Path
from openroad import Tech, Design
import ast, hashlib, json, re, struct, odb

C=Path('/work/week25_closure');R=Path('/work/routing')
for folder in ('inputs','reports','logs','runs'):(C/folder).mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
state=json.loads(Path('/work/week25_front/working_candidate_state.json').read_text())
source=Path(state['odb'])
assert sha(source)=='fe627dd4b1ff4c152dcfa9dd5d08b05c13b7272ab4065d7f0cb8af3d87dd1380'
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','guides','guide_sig','obstructions'})]:
    tree=ast.parse((R/'scripts'/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
lib=Path('/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib')
text=lib.read_text()
tree=ast.parse((R/'scripts/prepare_antenna_drive.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='logic')
exec(compile(ast.Module(body=[node],type_ignores=[]),'logic','exec'))
assert logic('sky130_fd_sc_hd__buf_1')!=logic('sky130_fd_sc_hd__nor2_2')
violations=json.loads(Path('/work/week25_signoff/reports/electrical_violations.json').read_text())
drivers={r['driver'].rsplit('/',1)[0]:r['driver_master'] for rows in violations['violations'].values() for r in rows}
assert len(drivers)==48
t=Tech();t.readLiberty(str(lib));t.readLiberty('/work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib')
design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock()
before=fixed(b);wire_before=wires(b);obs=obstructions(b)
removed=[]
for inst in list(b.getInsts()):
    if inst.getMaster().getName().startswith('sky130_fd_sc_hd__fill_'):
        removed.append(inst.getName());odb.dbInst_destroy(inst)
assert len(removed)==139324
unfilled=fixed(b);status={i.getName():str(i.getPlacementStatus()) for i in b.getInsts()}
affected=set();sizes={}
for name,old in sorted(drivers.items()):
    inst=b.findInst(name);assert inst and inst.getMaster().getName()==old
    stem,number=old.rsplit('_',1);new=stem+'_'+str(2*int(number))
    assert logic(old)==logic(new),(old,new)
    assert db.findMaster(new) is not None,new
    sizes[name]={'old':old,'new':new,'old_location':list(inst.getLocation()),'old_orientation':str(inst.getOrient())}
    for pin in inst.getITerms():
        if pin.getNet() and str(pin.getMTerm().getSigType()) not in ('POWER','GROUND'):affected.add(pin.getNet().getName())
    assert inst.swapMaster(db.findMaster(new)),name
# Freeze all other existing cells, and never run optimize_mirroring.
for inst in b.getInsts():
    if inst.getName() not in drivers:inst.setPlacementStatus('FIRM')
command='set e [catch {detailed_placement -max_displacement {50 50}; check_placement -verbose} msg]; list $e $msg'
answer=str(design.evalTclString(command))
assert answer.startswith('0 '),answer
for inst in b.getInsts():inst.setPlacementStatus(status[inst.getName()])
after=fixed(b)
changed={n for n in unfilled[0] if unfilled[0][n]!=after[0][n]}
assert changed==set(drivers),(changed-set(drivers),set(drivers)-changed)
for name in set(unfilled[0])-set(drivers):assert unfilled[0][name]==after[0][name],name
assert unfilled[1:]==after[1:] and obstructions(b)==obs
assert wires(b)==wire_before
for name in drivers:
    inst=b.findInst(name);sizes[name]['new_location']=list(inst.getLocation());sizes[name]['new_orientation']=str(inst.getOrient())
for name in affected:
    net=b.findNet(name)
    if net.getWire():odb.dbWire.destroy(net.getWire())
retained={name:digest for name,digest in wire_before.items() if name not in affected}
assert wires(b)==retained
partial=C/'inputs/minimal_partial.odb';global_input=C/'inputs/minimal_global.odb'
assert not partial.exists() and not global_input.exists()
odb.write_db(db,str(partial))
for net in b.getNets():
    if net.getWire():odb.dbWire.destroy(net.getWire())
assert not wires(b) and fixed(b)==after
odb.write_db(db,str(global_input))
clean={key:state[key] for key in ('nl','pnl','sdc','json_h','vh')}
clean['sdc']='/work/week25_signoff/constraints_reviewed.sdc'
clean.update(odb=str(global_input),metrics={})
(C/'global_state.json').write_text(json.dumps(clean,indent=2)+'\n')
record={'accepted':False,'source_sha256':sha(source),'partial_sha256':sha(partial),'global_sha256':sha(global_input),'resized':sizes,'same_function_and_pin_contract':True,'unrelated_cells_preserved':True,'logic_graph_and_PG_unchanged':True,'removed_fillers':len(removed),'cleared_nets':sorted(affected),'retained_wires':len(retained),'retained_wire_sha256':retained,'scope':'48 measured driver size changes only; all other original masters, placement, orientation, connectivity and native routes retained. Filler must be regenerated and every affected check rerun.'}
(C/'reports/minimal_input.json').write_text(json.dumps(record,indent=2)+'\n')
cfg=json.loads(Path('/work/week25_front/config_check.json').read_text())
cfg.update(DEFAULT_CORNER='max_tt_025C_1v80',STA_CORNERS=['max_tt_025C_1v80'],PNR_CORNERS=['max_tt_025C_1v80'],PL_OPTIMIZE_MIRRORING=False,DRT_THREADS=4)
cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc'
cfg['meta']={'version':2,'flow':['OpenROAD.GlobalRouting']}
(C/'config_global.json').write_text(json.dumps(cfg,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k not in ('retained_wire_sha256','resized')},indent=2),flush=True)
