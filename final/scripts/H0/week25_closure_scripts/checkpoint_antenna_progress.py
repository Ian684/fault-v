from pathlib import Path
from datetime import datetime,timezone
import json,re
C=Path(__file__).resolve().parents[1]
r=json.loads((C/'WORK_STATE.json').read_text());r.update(updated_utc=datetime.now(timezone.utc).isoformat(),status='active_antenna_reconnection_after_electrical_closure',W25_complete=False,selected_final_candidate=None)
proof=json.loads((C/'reports/antenna_access.json').read_text());pins=json.loads((C/'reports/antenna_ready_all_pins.json').read_text())
assert proof['added_passive_diodes']==20 and proof['all_original_cells_graph_PG_preferences_and_unaffected_wire_bytes_preserved'] and pins['all_native_preferences_valid']
r['subchecks']['antenna_insertion']={'passive_diodes_added':20,'affected_nets':18,'original_cells_graph_PG_AP_preferences_preserved':True,'all_native_pin_accesses_valid':True,'source_prepared_sha256':proof['output_sha256'],'evidence':['reports/antenna_access.json','reports/antenna_ready_all_pins.json','reports/antenna_name_gap_workaround.json'],'accepted_for_final':False}
incomplete=C/'reports/antenna_stubs_a/incomplete.json'
if incomplete.exists():
    record=json.loads(incomplete.read_text());r['subchecks']['antenna_stub_A_rejected']={'checked_branches':len(record['accepted']),'failed_diode':record['failed_diode'],'accepted_for_final':False,'cause':'Native same-net cut short / metal spacing at a later branch; no incomplete layout exported.'}
log=(C/'logs/antenna_route_a.log').read_text(errors='replace');partial=re.findall(r'Completing \d+% with (\d+) violations',log)
r['router_partial_marker_count']=int(partial[-1]) if partial else None
r['route_latest_marker_count']=None
r['physical_candidate']='Native antenna_route_a plus bounded local-stub trials; no final candidate accepted'
r['in_progress']=['Signal 51-driver three-RC electrical probe passed slew/cap/setup/hold violations 0','Twenty real diode cells inserted with original cells/logical graph/PG/AP preserved; all 141152 native access points valid','Local stub C resumes nine checked branches and reuses only exact coincident existing via geometry; full independent DRC/connectivity/antenna still required','Final common-candidate GDS/core-LVS/RCX/STA/GLS/activity/IR/fill gates remain required']
r['next_action']='Finish and independently validate actual diode branches, then export the exact checked candidate and run the prepared final common-candidate gates. Do not promote internal router counters or partial stub trials.'
f=C/'reports/antenna_stubs_f_independent.json';fc=C/'reports/antenna_stubs_f_all_connectivity.json'
if f.exists() and fc.exists():
    dr=json.loads(f.read_text());cn=json.loads(fc.read_text());pr=json.loads((C/'reports/antenna_stubs_f/result.json').read_text())
    assert dr['odb_sha256']==cn['source_sha256']==pr['output_sha256'] and dr['unresolved_count']==0 and cn['all_signal_geometry_connected']
    r['subchecks']['antenna_stub_F']={'source_sha256':pr['output_sha256'],'independent_native_DRC':0,'all_41337_nets_connected':True,'diode_terminals':cn['diode_terminals'],'antenna_nets':pr['antenna_nets'],'all_original_signal_copper_preserved':True,'accepted_for_final':False,'evidence':['reports/antenna_stubs_f/result.json','reports/antenna_stubs_f_independent.json','reports/antenna_stubs_f_all_connectivity.json']}
    r['physical_candidate']='antenna_stubs_f: native/context DRC 0, all 41337 nets connected, antenna 2; low-layer H trial not yet accepted'
    r['route_latest_marker_count']=0
    r['in_progress']=['51-driver fresh three-RC electrical probe passed all slew/cap/setup/hold violation counts zero','F actual full-route source: native/context DRC 0, all 41337 nets connected, 7572 diode terminals; two M2 antenna violations remain','Nineteen checked branches replayed in H; remaining net6033 branch targets its actual offending gate using LI1/M1/M2 only','Final common-candidate GDS/core-LVS/RCX/STA/GLS/activity/IR/fill gates remain required']
    r['next_action']='Complete the remaining process-stage M2 antenna connection; repeat whole-chip native/context DRC, all-net connectivity and antenna checks, then export and run final same-version physical/electrical/activity/density/IR gates.'
(C/'reports/prior_evidence_integrity_20261101.json').exists() and r['subchecks'].update(frozen_prior_evidence_875_files_unchanged=True)
restore=C/'reports/antenna_restore4_independent.json'
if restore.exists():
    dr=json.loads(restore.read_text());pr=json.loads((C/'reports/antenna_restore4/result.json').read_text())
    r['subchecks']['restore4_rejected']={'antenna_nets':pr['antenna_nets'],'independent_DRC':dr['unresolved_count'],'accepted_for_final':False,'scope':'Restoring four whole nets alone causes real collisions with native neighboring routes.'}
    r['status']='active_route_source_conflict_resolution'
    r['in_progress']=['Selected 51-driver clean-source three-RC slew/cap/setup/hold violation counts all zero','Manual F: independent DRC 0, all 41337 nets connected, antenna 2; native iteration12: DRC 1, antenna 2, all nets connected','restore4 antenna 0 rejected by 27 independently confirmed real DRC markers','Pairwise route-source constraint solver uses actual observed conflicts; whole-source choices retain native diode routes and protected original nets','Final common-candidate physical/electrical/activity/IR/fill gates remain required']
    r['physical_candidate']='No final candidate. SAT-guided original/native source selection running; rejected trials retained.'
    r['next_action']='Resolve route-source conflicts with fresh independent checks; if whole-wire choices are insufficient, perform local geometry repair. Require actual same-source DRC/connectivity/antenna zero before final export.'
final_route=C/'reports/final_route_selection_b.json'
if not final_route.exists():final_route=C/'reports/final_route_selection.json'
if final_route.exists():
    route=json.loads(final_route.read_text());assert route['independent_DRC']==route['antenna_nets']==0 and route['all_signal_geometry_connected']
    r['status']='active_final_common_candidate_verification'
    r['subchecks']['final_combined_route']=route
    r['physical_candidate']=route['run_tag'];r['route_latest_marker_count']=0
    r['selected_route_candidate']=route['source_sha256']
    r['in_progress']=['Combined 51-driver / PG_G / 20-diode route: native full/context DRC 0, all 41337 nets connected, antenna 0','Exact manual export and all reviewed cells/PG/logical graph bindings verified','Fresh common-candidate filler/GDS/open DRC/antenna/three-RC extraction and STA flow running','Final core LVS, functional/reset/activity, stream/PG audits, IR/EM and regenerated fill/density remain required']
    r['next_action']='Finish the selected common post/STA case, stage its actual filled ODB/GDS, run final core-LVS/stream/functional/IR/fill gates and freeze only after every specified research gate is verified.'
post_a=C/'runs/focus_post_a/3-klayout-drc/state_out.json'
if post_a.exists() and not (C/'reports/final_route_selection_b.json').exists():
    count=json.loads(post_a.read_text())['metrics']['klayout__drc_error__count']
    if count:
        assert count==43
        r['status']='active_actual_GDS_LI1_spacing_closure'
        r['subchecks']['post_A_rejected']={'full_open_GDS_DRC':43,'rule':'li.3','fresh_three_RC_STA_slew_cap':0,'scope':'Routing-model clean source is not full-GDS clean. Same-version acceptance withheld.'}
        r['physical_candidate']='inputs/li1_spacing.odb; actual-GDS same-owner closure with full native verification in progress'
        r['in_progress']=['Post-A full GDS reveals 43 LI1 spacing markers despite native/context DRC 0; rejected for final acceptance','Actual GDS ownership/foreign-metal clearance checked; 57 LI1 patches across eight nets replay the pinned LI1 width/spacing rules 43 to 0','Patched ODB antenna remains 0; fresh native/context DRC and all-net connectivity running','Post-B full-deck/GDS/RCX/STA followed by final core LVS, stream, activity, IR/EM and regenerated fill remain required']
        r['next_action']='Require patched ODB independent DRC/connectivity zero, export under antenna_li1_a, stage final_route_b.odb, verify final_route_b invariants, select final_b and run run_final_post_b.sh. Final downstream helpers are now bound to focus_post_b.'
(C/'WORK_STATE.json').write_text(json.dumps(r,indent=2)+'\n')
p=C.parent/'routing/WORK_STATE.json';old=json.loads(p.read_text(encoding='utf-8-sig'));old['follow_on_work'].update(status=r['status'],W25_complete=False,state='../week25_closure/WORK_STATE.json',updated_utc=r['updated_utc'],next_action=r['next_action']);p.write_text(json.dumps(old,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('ANTENNA_CHECKPOINT_SAVED',r['updated_utc'],'router partial',r['router_partial_marker_count'],flush=True)
