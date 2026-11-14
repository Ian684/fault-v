"""Restore four unaffected nets from the verified source; retain native diode routes."""
from pathlib import Path
import hashlib,json,shutil,sys,odb
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,primitives
C=Path('/work/week25_closure');source=Path('/native/drt_iter12.odb')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
probe=json.loads((C/'reports/antenna_iter12_probe.json').read_text());assert sha(source)==probe['source_sha256']
cn=json.loads((C/'reports/antenna_iter12_all_connectivity.json').read_text());assert cn['source_sha256']==probe['source_sha256'] and cn['all_signal_geometry_connected']
t=Tech();design=Design(t);design.readDb(str(source));db=design.getDb();b=db.getChip().getBlock()
rd,rb=load('/runtime_final/focus_pg.odb');reference=json.loads((C/'reports/focus_pg_rebase.json').read_text());assert sha(Path('/runtime_final/focus_pg.odb'))==reference['output_sha256']
names={'net3347','net5547','net2682','net8704'}
access=json.loads((C/'reports/antenna_access.json').read_text());assert not names&set(access['diode_affected_nets'])
before=fixed(b);oldw=wires(b);oldg=guides(b);oldo=obstructions(b);refw=wires(rb)
for name in sorted(names):
    net=b.findNet(name);original=rb.findNet(name);assert net and original and str(net.getSigType())=='SIGNAL'
    assert before[1][name]==fixed(rb)[1][name]
    odb.dbWire.destroy(net.getWire());w=odb.dbWire.create(net);w.append(original.getWire())
    assert primitives(w)[0]==primitives(original.getWire())[0]
after=wires(b);assert all(after[n]==refw[n] for n in names)
assert {n:v for n,v in after.items() if n not in names}=={n:v for n,v in oldw.items() if n not in names}
assert fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo and len(after)==41337
out=C/'reports/antenna_restore4';out.mkdir(exist_ok=False)
antenna=int(design.evalTclString('check_antennas -report_file '+str(out/'antenna.rpt')))
native=Path('/runtime_final/antenna_restore4.odb');target=C/'inputs/antenna_restore4.odb';assert not native.exists() and not target.exists();odb.write_db(db,str(native))
with native.open('rb') as inp,target.open('xb') as f:shutil.copyfileobj(inp,f,1024*1024)
assert sha(native)==sha(target)
(out/'result.json').write_text(json.dumps({'source_snapshot_sha256':probe['source_sha256'],'reference_original_signal_sha256':reference['output_sha256'],'output_sha256':sha(native),'restored_unaffected_nets':sorted(names),'all_other_signal_wire_bytes_preserved':True,'cells_graph_PG_guides_obstructions_unchanged':True,'antenna_nets':antenna,'passive_diodes_added':20,'accepted_for_final':False,'scope':'Native diode-route snapshot with four non-diode nets restored exactly from the independently clean original geometry. Full same-source DRC/connectivity and all final gates still required.'},indent=2)+'\n')
print('UNAFFECTED_NET_RESTORE_CANDIDATE',sha(native),'antenna',antenna,flush=True)
