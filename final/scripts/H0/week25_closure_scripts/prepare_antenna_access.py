"""Validate passive insertion, preserve original objects and reuse proven native accesses."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,re,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,path_type
C=Path('/work/week25_closure');source=Path('/runtime/antenna_inserted.odb');reference=Path('/runtime_final/focus_pg.odb')
tag=sys.argv[1];assert re.fullmatch('[a-z0-9_]+',tag);run=C/'runs'/tag/'1-openroad-detailedrouting'
proof=json.loads((run/'insertion.json').read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==proof['output_sha256']
assert sha(reference)==json.loads((C/'reports/focus_pg_rebase.json').read_text())['output_sha256']
db,b=load(source);rd,rb=load(reference);before=fixed(rb);after=fixed(b)
new=set(after[0])-set(before[0]);assert 0<=len(new)<=200
assert {n:v for n,v in after[0].items() if n not in new}==before[0],'An original cell was moved/resized/removed'
assert after[2]==before[2] and obstructions(b)==obstructions(rb),'PG or block geometry changed during insertion'
assert {n:(v[0],tuple(t for t in v[1] if t[0] not in new),v[2]) for n,v in after[1].items()}==before[1],'Original logical connectivity changed'
old_wires=wires(rb);now=wires(b);assert len(old_wires)==41337
violators=set(re.findall(r'^Net:\s+(\S+)',(run/'baseline_antenna.rpt').read_text(),re.M))
assert len(violators)==proof['baseline_antenna_nets']
affected=set()
for name in new:
    i=b.findInst(name);assert i.getMaster().getName()=='sky130_fd_sc_hd__diode_2'
    signal=i.findITerm('DIODE').getNet();assert signal and signal.getName() in violators;affected.add(signal.getName())
    for p in i.getITerms():
        kind=str(p.getMTerm().getSigType())
        if kind in ('POWER','GROUND'):assert p.getNet() and p.getNet().getName()==('VPWR' if kind=='POWER' else 'VGND')
assert {n:v for n,v in now.items() if n not in affected}=={n:v for n,v in old_wires.items() if n not in affected}
pg_check=json.loads((C/'reports/focus_pg_independent.json').read_text())
assert pg_check['odb_sha256']==json.loads((C/'reports/focus_pg_rebase.json').read_text())['output_sha256']
assert 0<=pg_check['unresolved_count']<=30
pg_signal=set()
for marker in pg_check['unresolved']:
    names=set(re.findall(r'net:([^\s]+)',marker['srcs']))
    assert len(names&{'VPWR','VGND'})==1 and len(names)==2
    pg_signal.update(names-{'VPWR','VGND'})
assert all(str(b.findNet(n).getSigType()) in ('SIGNAL','CLOCK') for n in pg_signal)
repair_nets=affected|pg_signal
def preferences(block,exclude):
    return {(i.getName(),p.getMTerm().getName()):(i.getPinAccessIdx(),tuple(sorted((a.getLayer().getName(),tuple(a.getPoint())) for a in p.getPrefAccessPoints()))) for i in block.getInsts() if i.getName() not in exclude for p in i.getITerms()}
assert preferences(b,new)==preferences(rb,set()),'Original native access preferences changed'
peers=defaultdict(list)
for i in b.getInsts():
    if i.getName() not in new:peers[(i.getMaster().getName(),str(i.getOrient()))].append(i)
borrowed={}
for name in sorted(new):
    inst=b.findInst(name);x,y=inst.getLocation();chosen=None
    for peer in peers[(inst.getMaster().getName(),str(inst.getOrient()))]:
        px,py=peer.getLocation()
        if (x-px)%460 or (y-py)%340:continue
        points=list(peer.findITerm('DIODE').getPrefAccessPoints())
        if points and all(any(l.getName()==a.getLayer().getName() and z.xMin()<=x+a.getPoint()[0]<=z.xMax() and z.yMin()<=y+a.getPoint()[1]<=z.yMax() for l,z in inst.findITerm('DIODE').getGeometries()) for a in points):chosen=peer;break
    assert chosen,('No valid same-phase/orientation native diode access peer',name)
    inst.setPinAccessIdx(chosen.getPinAccessIdx())
    for pin in inst.getITerms():
        pin.clearPrefAccessPoints()
        for a in chosen.findITerm(pin.getMTerm().getName()).getPrefAccessPoints():pin.setAccessPoint(a.getMPin(),a)
    borrowed[name]={'peer':chosen.getName(),'orientation':str(inst.getOrient()),'location':list(inst.getLocation()),'signal_net':inst.findITerm('DIODE').getNet().getName()}
assert preferences(b,new)==preferences(rb,set())
for name in repair_nets:
    n=b.findNet(name)
    if n.getWire():odb.dbWire.destroy(n.getWire())
assert wires(b)=={n:v for n,v in old_wires.items() if n not in repair_nets}
assert all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
native=Path('/runtime_final/antenna_ready.odb');out=C/'inputs/antenna_ready.odb';assert not native.exists() and not out.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,out.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
digest=sha(native);assert sha(out)==digest
state=json.loads((run/'state_out.json').read_text());state.update(odb=str(native),metrics={},sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('gds','klayout_gds','spef','def'):state.pop(key,None)
(C/'antenna_route_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_working.json').read_text());cfg['meta']={'version':2,'flow':['OpenROAD.DetailedRouting']};cfg.update(DRT_THREADS=4,DRT_OPT_ITERS=32)
cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc'
(C/'config_antenna_route.json').write_text(json.dumps(cfg,indent=2)+'\n')
audit=(C/'scripts/audit_cached_pins.py').read_text().replace("C/'inputs/cached_guided.odb'","Path('/runtime_final/antenna_ready.odb')").replace('reports/cached_all_pins.json','reports/antenna_ready_all_pins.json')
assert '/runtime_final/antenna_ready.odb' in audit;(C/'scripts/audit_antenna_ready_pins.py').write_text(audit)
record={'source_sha256':sha(source),'reference_sha256':sha(reference),'output_sha256':digest,'added_passive_diodes':len(new),'borrowed_native_accesses':borrowed,'diode_affected_nets':sorted(affected),'PG_signal_interaction_nets':sorted(pg_signal),'cleared_signal_nets':sorted(repair_nets),'all_original_cells_graph_PG_preferences_and_unaffected_wire_bytes_preserved':True,'accepted_for_final':False,'scope':'Real diode cells and same-master/orientation/site-phase native APs. Complete diode nets plus actual independently measured combined-candidate PG/signal interaction nets cleared for physical reconnection; all final connectivity/DRC/LVS/antenna/electrical checks remain required.'}
(C/'reports/antenna_access.json').write_text(json.dumps(record,indent=2)+'\n');print('ANTENNA_ACCESS_READY',len(new),len(affected),digest,flush=True)
