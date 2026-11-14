"""Select only a hash-coherent, independently DRC-clean and connected signal layout."""
from pathlib import Path
import hashlib,json,re,sys
C=Path(__file__).resolve().parents[1];tag=sys.argv[1];assert re.fullmatch('[a-z0-9_]+',tag)
run=C/'runs'/tag/'1-openroad-detailedrouting'
assert (C/'logs'/f'{tag}.exit').read_text().strip()=='0'
pair=json.loads((run/'native_pair.json').read_text());independent=C/'reports'/sys.argv[2];connectivity=C/'reports'/sys.argv[3]
driver51=len(sys.argv)>4 and sys.argv[4]=='driver51'
mode=sys.argv[4] if len(sys.argv)>4 else None;final=mode in ('final','final_b','final_c')
suffix=('_'+mode.rsplit('_',1)[1]) if mode in ('final_b','final_c') else ''
assert independent.parent==connectivity.parent==C/'reports'
dr=json.loads(independent.read_text());cn=json.loads(connectivity.read_text())
with (run/'native_final.odb').open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
assert pair['odb_sha256']==dr['odb_sha256']==cn['source_sha256']==digest
assert pair['native_DRC']==dr['unresolved_count']==0 and cn['all_signal_geometry_connected']
if pair.get('native_DRC_authority')=='independent_native_full_context':
    binding_name=(tag+'_export_binding.json' if (C/'reports'/(tag+'_export_binding.json')).exists() else 'final_manual_export_binding.json') if final else ('manual_export51_binding.json' if driver51 else 'manual_export_binding.json')
    binding=json.loads((C/'reports'/binding_name).read_text())
    assert binding['native_final_sha256']==digest and binding['all_exported_cells_graph_PG_wire_bytes_guides_obstructions_equal_checked_source']
assert cn['checked_multi_terminal_signal_clock_nets']>40000 and not cn['bad_nets'] and not cn['missing_wires']
stage_name=('final_route'+suffix) if final else ('signal_closed_51' if driver51 else 'signal_closed')
stage=json.loads((C/'reports'/f'runtime_{stage_name}_odb.json').read_text());assert stage['sha256']==digest
if final:
    assert pair['antenna_nets']==0
    inv=json.loads((C/'reports'/('final_route'+suffix+'_invariants.json')).read_text())
    assert inv['source_sha256']==digest and inv.get('all_original_cells_graph_PG_and_obstructions_unchanged',inv['cells_graph_PG_and_obstructions_unchanged'])
record={'run_tag':tag,'source_sha256':digest,'independent_DRC':0,'all_signal_geometry_connected':True,'antenna_nets':pair['antenna_nets'],'independent_report':independent.relative_to(C).as_posix(),'connectivity_report':connectivity.relative_to(C).as_posix(),'runtime_ODB':'/runtime/'+stage_name+'.odb','accepted_for_final':False,'scope':'Signal-only selection. PG rebasing, antenna repair and all final gates remain required.'}
if final:
    assert inv['reviewed_driver_count']==51 and inv['all_reviewed_driver_masters_preserved']
    record.update(reviewed_driver_count=51,PG_variant='PG_G',added_passive_diodes=20,reviewed_added_passive_diode_relocations=inv.get('reviewed_added_passive_diode_relocations',[]),scope='Combined 51-driver / PG_G / 20-diode route with independent DRC, all-net connectivity and antenna zero. Any reviewed relocation is limited to four newly inserted passive diodes. Final filler/GDS/core-LVS/RCX/STA/functional/activity/IR/fill gates remain required.')
target=C/'reports'/(('final_route_selection'+suffix+'.json') if final else 'signal_selection.json')
if driver51:
    overlay=json.loads((C/'reports/driver51_trial_b.json').read_text());prior=json.loads(target.read_text())
    assert prior['source_sha256']==overlay['source_sha256'] and digest==overlay['output_sha256']
    history=C/'reports/signal_selection_50.json';assert not history.exists();history.write_bytes(target.read_bytes())
    record.update(driver_overlay='reports/driver51_trial_b.json',previous_source_sha256=prior['source_sha256'])
else:assert not target.exists()
partial=target.with_suffix('.json.part');assert not partial.exists();partial.write_text(json.dumps(record,indent=2)+'\n');partial.replace(target)
print('SIGNAL_CANDIDATE_SELECTED',tag,digest,flush=True)
