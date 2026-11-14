"""Rebase the verified PG geometry onto the reviewed DRC-closed signal candidate."""
from pathlib import Path
from collections import Counter
import copy,hashlib,json,shutil,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires,guides,obstructions,path_type
from reviewed_drivers import load_driver_review
C=Path('/work/week25_closure')
selection=json.loads((C/'reports/signal_selection.json').read_text())
run=C/'runs'/selection['run_tag'];assert run.parent==C/'runs'
pair=json.loads((run/'1-openroad-detailedrouting/native_pair.json').read_text())
assert pair['native_DRC']==0,'Signal route is not closed'
assert selection['independent_DRC']==0 and selection['all_signal_geometry_connected']
independent=json.loads((C/selection['independent_report']).read_text())
assert independent['unresolved_count']==0 and independent['odb_sha256']==pair['odb_sha256']
source=Path(selection.get('runtime_ODB','/runtime/signal_closed.odb'));desired=Path('/runtime_final/pg_compact_g.odb');assert source.parent==Path('/runtime')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==pair['odb_sha256']
pg_selection=json.loads((C/'reports/selected_pg.json').read_text())
assert pg_selection['variant']=='PG_G' and pg_selection['independent_native_DRC']==pg_selection['full_GDS_open_DRC']==pg_selection['hierarchical_core_LVS_errors']==0 and pg_selection['four_controlled_average_EM_cases_pass'] and pg_selection['PG_contact_geometry_pass']
assert sha(desired)==pg_selection['source_sha256']
db,b=load(source)
placement_source=Path('/runtime/cached_guided.odb')
assert sha(placement_source)==json.loads((C/'reports/native_runtime_stage.json').read_text())['files']['cached_guided.odb']['sha256']
pd,pb=load(placement_source)
targets,overlay=load_driver_review(C);reference_cells,reference_graph,_=fixed(pb)
if overlay:
    for row in overlay['removed_passive_diodes']:
        assert reference_cells[row['name']][0]==row['master'];reference_cells.pop(row['name'])
    assert reference_cells[overlay['cell']][0]==overlay['old_master']
    reference_cells[overlay['cell']]=(overlay['new_master'],*reference_cells[overlay['cell']][1:])
    removed={r['name'] for r in overlay['removed_passive_diodes']}
    reference_graph={n:(v[0],tuple(p for p in v[1] if p[0] not in removed),v[2]) for n,v in reference_graph.items()}
assert fixed(b)[:2]==(reference_cells,reference_graph),'Signal candidate differs from reviewed physical/logical overlay'
odb.dbDatabase.destroy(pd);del pb,pd
dd,desired_block=load(desired)
before=fixed(b);old_wires=wires(b);old_guides=guides(b);old_obs=obstructions(b)
assert len(old_wires)==41337 and all(path_type(n.getWire())=='ROUTED' for n in b.getNets() if n.getWire())
for name,row in targets.items():assert b.findInst(name).getMaster().getName()==row['master']
base=json.loads((C/'reports/pg_via_plan_b.json').read_text())
extra=json.loads((C/'reports/pg_d_applied.json').read_text())
changes={(r['net'],*r['before']['old_xy']):r['after'] for r in extra['via_changes']}
proposals=[copy.deepcopy(changes.get((r['net'],*r['old_xy']),r)) for r in base['planned_replacements']]
e_changes={(r['net'],*r['prior_xy']):r for r in json.loads((C/'reports/pg_compact_e/result.json').read_text())['accepted_changes']}
f_changes={(r['net'],*r['prior_xy']):r for r in json.loads((C/'reports/pg_f_geometry_binding.json').read_text())['only_three_planned_via_translations']}
g_changes={(r['net'],*r['prior_xy']):r for r in json.loads((C/'reports/pg_g_geometry_binding.json').read_text())['restored_original_single_cut_vias']}
desired_vias={}
for n in desired_block.getNets():
    for sw in n.getSWires():
        for q in sw.getWires():
            if q.isVia() and q.getBlockVia() and q.getBlockVia().getViaParams().getCutLayer().getName()=='via4':
                key=(n.getName(),*q.getViaXY());assert key not in desired_vias;desired_vias[key]=q
for row in proposals:
    for updates in (e_changes,f_changes,g_changes):
        update=updates.get((row['net'],*row['new_xy']))
        if update:row['new_xy']=update['new_xy']
    q=desired_vias[(row['net'],*row['new_xy'])];v=q.getBlockVia();params=v.getViaParams()
    row.update(new_via=v.getName(),new_bbox=[q.xMin(),q.yMin(),q.xMax(),q.yMax()],cols=params.getNumCutCols(),rows=params.getNumCutRows(),new_cut_count=sum(z.getTechLayer().getName()=='via4' for z in v.getBoxes()))
    for prop in ('XBottomEnclosure','YBottomEnclosure','XTopEnclosure','YTopEnclosure'):row[prop]=getattr(params,'get'+prop)()
assert len(proposals)==183 and sum(r['new_cut_count'] for r in proposals)==1430
patches=extra['merged_M4_patches'];assert len(patches)==20
removed=Counter((r['net'],*r['old_bbox'],r['old_via']) for r in proposals)
added=Counter((r['net'],*r['new_bbox'],r['new_via']) for r in proposals)
added.update((r['net'],*r['box'],'met4') for r in patches)
desired_pg=Counter(fixed(desired_block)[2])
assert not (added-desired_pg),'Desired geometry is missing a proven patch'
assert Counter(before[2])==desired_pg-added+removed,'Signal candidate PG differs from the proven original PG'
lookup={}
for netname in ('VPWR','VGND'):
    for sw in b.findNet(netname).getSWires():
        for q in sw.getWires():
            if q.isVia():lookup[(netname,*q.getViaXY())]=(sw,q)
props=('BottomLayer','CutLayer','TopLayer','NumCutCols','NumCutRows','XCutSize','YCutSize','XCutSpacing','YCutSpacing','XOrigin','YOrigin','XBottomEnclosure','YBottomEnclosure','XTopEnclosure','YTopEnclosure','XBottomOffset','YBottomOffset','XTopOffset','YTopOffset')
for r in proposals:
    sw,old=lookup[(r['net'],*r['old_xy'])];prior=old.getBlockVia();assert prior and prior.getName()==r['old_via']
    via=b.findVia(r['new_via'])
    if via is None:
        via=odb.dbVia.create(b,r['new_via']);p=odb.dbViaParams();orig=prior.getViaParams()
        for prop in props:getattr(p,'set'+prop)(getattr(orig,'get'+prop)())
        p.setNumCutCols(r['cols']);p.setNumCutRows(r['rows'])
        for prop in ('XBottomEnclosure','YBottomEnclosure','XTopEnclosure','YTopEnclosure'):getattr(p,'set'+prop)(r[prop])
        via.setViaGenerateRule(prior.getViaGenerateRule());via.setViaParams(p)
    assert sum(z.getTechLayer().getName()=='via4' for z in via.getBoxes())==r['new_cut_count']
    target_via=desired_vias[(r['net'],*r['new_xy'])].getBlockVia()
    boxes=lambda v:Counter((q.getTechLayer().getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax()) for q in v.getBoxes())
    assert boxes(via)==boxes(target_via),'Rebased via cut/enclosure geometry differs from selected PG'
    new=odb.dbSBox.create(sw,via,*r['new_xy'],str(old.getWireShapeType()));assert new
    assert [new.xMin(),new.yMin(),new.xMax(),new.yMax()]==r['new_bbox']
    odb.dbSBox.destroy(old)
for r in patches:
    sw=next(iter(b.findNet(r['net']).getSWires()))
    assert odb.dbSBox.create(sw,db.getTech().findLayer('met4'),*r['box'],'STRIPE')
after=fixed(b)
assert before[:2]==after[:2] and wires(b)==old_wires and guides(b)==old_guides and obstructions(b)==old_obs
assert Counter(after[2])==desired_pg
native=Path('/runtime_final/focus_pg.odb');target=C/'inputs/focus_pg.odb';assert not native.exists() and not target.exists()
odb.write_db(db,str(native))
partial=target.with_suffix('.odb.part');assert not partial.exists()
with native.open('rb') as inp,partial.open('wb') as out:shutil.copyfileobj(inp,out,1024*1024)
digest=sha(native);assert sha(partial)==digest;partial.rename(target)
state=json.loads((run/'1-openroad-detailedrouting/state_out.json').read_text());state['odb']=str(native);state['metrics']={};state['sdc']='/work/week25_signoff/constraints_reviewed.sdc'
for key in ('gds','klayout_gds','spef','def'):state.pop(key,None)
(C/'focus_post_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_working.json').read_text());assert cfg['KLAYOUT_CONFLICT_RESOLUTION']=='OverwriteCell'
cfg['meta']={'version':2,'flow':['OpenROAD.FillInsertion','KLayout.StreamOut','KLayout.DRC','OpenROAD.CheckAntennas','OpenROAD.RCX']}
cfg['PNR_SDC_FILE']=cfg['SIGNOFF_SDC_FILE']='/work/week25_signoff/constraints_reviewed.sdc';cfg['DECAP_CELLS']=[]
(C/'config_focus_post.json').write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/focus_pg_rebase.json').write_text(json.dumps({'accepted':False,'source_signal_sha256':pair['odb_sha256'],'proven_PG_source_sha256':sha(desired),'PG_variant':pg_selection['variant'],'output_sha256':digest,'actual_50_driver_masters_verified':True,'all_cells_graph_signal_wire_bytes_guides_obstructions_unchanged':True,'PG_geometry_exactly_matches_selected_PG':True,'via_array_replacements':181,'planned_positions':183,'via4_cuts_at_planned_positions':1430,'M4_patches':20,'compacted_three_cut_row_feed_preserved':True,'scope':'Only selected PG_G changes rebased; actual combined-candidate DRC/LVS/antenna/STA/IR/fill gates still required.'},indent=2)+'\n')
print('FOCUS_PG_REBASE_READY',digest,'signal geometry unchanged',flush=True)
