"""Record completed subchecks separately from final candidate acceptance."""
from pathlib import Path
from datetime import datetime,timezone
import json,re
C=Path(__file__).resolve().parents[1]
r=json.loads((C/'WORK_STATE.json').read_text())
pg=json.loads((C/'reports/pg_d_em_resistor_audit.json').read_text())
density=json.loads((C/'reports/dense_fom_native_b_density.json').read_text())
fom=json.loads((C/'reports/full_fom_b_geometry.json').read_text())
filled=json.loads((C/'reports/dense_b_verified.json').read_text())
assert filled['full_BEOL_marker_count']==0 and all(filled['all_six_dummy_width_negative_controls_detected'].values())
dr=json.loads((C/'runs/pg_stream_d/2-klayout-drc/state_out.json').read_text())
assert pg['native_average_current_screen_pass'] and density['all_numeric_density_checks_pass'] and fom['screen_pass'] and dr['metrics']['klayout__drc_error__count']==0
sta=json.loads((C/'runs/probe50_sta_a/1-openroad-staprepnr/state_out.json').read_text())['metrics']
projected=json.loads((C/'runs/projected67_sta_a/1-openroad-staprepnr/state_out.json').read_text())['metrics']
local_sta=json.loads((C/'runs/focus_probe_sta_a/1-openroad-staprepnr/state_out.json').read_text())['metrics']
assert local_sta['design__max_slew_violation__count']==local_sta['design__max_cap_violation__count']==0
assert projected['design__max_slew_violation__count']==projected['design__max_cap_violation__count']==0
r.update(updated_utc=datetime.now(timezone.utc).isoformat(),W25_complete=False,foundry_signoff_complete=False,selected_final_candidate=None,status='active_signal_route_electrical_and_fill_interaction_closure')
r['subchecks']={
 'PG_D':{'complete_for_controlled_F_baseline':True,'full_GDS_open_DRC':0,'native_average_EM_violations_all_four_cases':0,'peak_EM_limit_utilization':max(v['utilization'] for case in pg['cases'].values() for net in case.values() for v in net['worst_per_layer'].values()),'via_arrays':183,'total_via4_cuts':1444,'widened_M4_patches':20,'source_ODB':'inputs/pg_via_d.odb','source_sha256':json.loads((C/'reports/pg_d_applied.json').read_text())['output_ODB_sha256'],'evidence':['reports/pg_d_applied.json','reports/pg_d_em_resistor_audit.json','runs/pg_stream_d/2-klayout-drc/state_out.json'],'final_signal_candidate':False},
 'density_B':{'source':'corrected + trimmed original F baseline, before drive/PG fixes','all_seven_numeric_layers_pass_1053_windows_each':True,'FOM_global':density['layers']['FOM']['global_after'],'FOM_min':density['layers']['FOM']['window_min'],'FOM_full_geometry_pass':True,'full_BEOL_fill_interaction':'running, not yet accepted','evidence':['reports/dense_fom_native_b_density.json','reports/full_fom_b_geometry.json'],'final_signal_candidate':False},
 'physical_50_driver_probe':{'source':'stable full_route_a iteration 13, diagnostic only','max_RC_slew_violations':sta['design__max_slew_violation__count'],'max_RC_cap_violations':sta['design__max_cap_violation__count'],'fresh_three_RC_extractions':True,'final_acceptance':False},
 'projected_67_driver_STA':{'all_three_RC_slew_cap_violations':0,'setup_hold_positive':True,'physical_ECO_applied':False,'scope':'Analysis-only old-wire size selection; cannot replace fresh post-ECO extraction','evidence':'reports/projected67_input.json'},
}
r['subchecks']['density_B'].update(full_BEOL_fill_interaction_markers=0,full_BEOL_fill_interaction='complete for development baseline; not final signal candidate',all_six_dummy_width_negative_controls_detected=True)
r['subchecks']['density_B']['evidence'].append('reports/dense_b_verified.json')
r['subchecks']['physical_50_driver_local_probe']={'source':'focus_unfixed_a iteration 9, diagnostic only','fresh_three_RC_extractions':True,'all_three_RC_slew_cap_violations':0,'worst_setup_ns':local_sta['timing__setup__ws'],'worst_hold_ns':local_sta['timing__hold__ws'],'final_acceptance':False,'source_sha256':'8dbd1cac6e8311a74aa79a9cc110415207f98e60e1b6ac44f6d03b53d07ccd36'}
r['installed_skills']={'names':['openroad-tcl','sdc-sta','verification-before-completion'],'durable_root':'E:/Codex/Skills','global_registration':'<HOME>/.codex/skills','manifest':'E:/Codex/Skills/INSTALL_MANIFEST.json','ponytail_preserved':True}
text=(C/'logs/full_route.log').read_text(errors='replace');m=re.findall(r'Completing \d+% with (\d+) violations',text)
r['full_route_last_marker_count']=int(m[-1]);r['physical_candidate']='runs/focus_unfixed_a'
focus=(C/'logs/focus_unfixed.log').read_text(errors='replace');fm=re.findall(r'Completing \d+% with (\d+) violations',focus)
r['route_latest_marker_count']=int(fm[-1]) if fm else None
r['in_progress']=['75-net conflict-cover retry with native cached AP audit and all neighboring routes editable; completed local iteration-9 snapshot has fresh three-RC slew/cap 0','Final merge of verified PG/density and actual electrical/route candidate, followed by fresh final gates']
for item in ['PG_D actual 183-array + 20-M4-patch candidate: full-GDS KLayout DRC 0 and native average-current EM 0 at 14/28mW per SRAM','Density B: all 1053 windows of FOM/LI/M1-5 pass; all 20 FOM local geometry tiles pass','Projected 67-driver analysis-only STA has slew/cap 0 at all three RC conditions; no physical ECO acceptance implied']:
    if item not in r['completed']:r['completed'].append(item)
for item in ['protected_cached_a stopped after 27881 initial DRVs; pin-cache preservation did not resolve FIXED-route issues','PG_C stress average-current screen still has one M4 violation; superseded by PG_D','projected67 STA is a size-selection model, not a routed or signoff candidate']:
    if item not in r['not_promoted']:r['not_promoted'].append(item)
item='full_route_a stopped with 791 DRVs and 157/17 max-RC probe violations; completed iteration snapshots retained for fallback'
if item not in r['not_promoted']:r['not_promoted'].append(item)
r['fallback_route_snapshots']='runs/full_route_a/1-openroad-detailedrouting/drt_iter*.odb'
r['next_action']='Finish native signal-route closure on the actual 50-driver local candidate; merge verified PG_D, regenerate final fill, and rerun extraction, STA/LVS/antenna/activity/IR checks. The projected 17 extra drivers are not required by the local candidate probe and have not been physically applied.'
independent=json.loads((C/'reports/focus_finish_independent.json').read_text())
pair=json.loads((C/'runs/focus_finish_a/1-openroad-detailedrouting/native_pair.json').read_text())
assert independent['odb_sha256']==pair['odb_sha256']
r['subchecks']['focus_finish_rejected']={'router_reported_DRC':pair['native_DRC'],'independent_unresolved_DRC':independent['unresolved_count'],'raw_markers':independent['raw_marker_count'],'confirmed_partition_artifacts':independent['confirmed_partition_artifacts'],'antenna_nets':pair['antenna_nets'],'source_sha256':pair['odb_sha256'],'accepted':False,'evidence':'reports/focus_finish_independent.json'}
grid=json.loads((C/'reports/dummy_grid_b.json').read_text())
assert len(grid['layers'])==8 and all(x['offgrid_markers']==0 for x in grid['layers'].values())
r['subchecks']['density_B']['all_eight_fill_layers_on_5nm_grid']=True
r['subchecks']['density_B']['evidence'].append('reports/dummy_grid_b.json')
r['physical_candidate']='runs/short_cover_a'
r['route_latest_marker_count']=independent['unresolved_count']
r['in_progress']=['Five-net cover of all seven independently confirmed shorts; complete neighbors remain ROUTED and editable','Core LVS probe pg_d_lvs_d uses corrected full-macro GDS and original abstract-SRAM scope, native working directory, and SHA-verified archive','Final common-candidate PG/antenna/electrical/fill/verification gates remain required']
r['next_action']='Finish the five-net short repair and independently recheck actual geometry; reject the focus_finish_a internal zero counter because independent checking still finds seven shorts. Then merge proven PG_D, repair antenna, and rerun all final gates.'
item='focus_finish_a internal DRC counter 0 rejected: independent full-chip/context check finds seven real shorts; antenna 19'
if item not in r['not_promoted']:r['not_promoted'].append(item)
cn=json.loads((C/'reports/focus_unfixed_all_connectivity.json').read_text())
assert cn['checked_multi_terminal_signal_clock_nets']==41337 and [x['net'] for x in cn['bad_nets']]==['net3116']
r['subchecks']['signal_connectivity_before_repair']=cn
r['physical_candidate']='runs/short_cover_b'
r['in_progress']=['Six-net repair: five-net short cover plus independently confirmed inherited open net3116, using the actual focus_unfixed final source; native iteration snapshots enabled','Core LVS pg_d_lvs_f: full source geometry with 268 exact duplicate unlabeled SRAM instances removed; all 39 mask layers and text labels equal','Final common-candidate PG/antenna/electrical/fill/verification gates remain required']
dedup=json.loads((C/'reports/macro_dedup.json').read_text())
r['subchecks']['SRAM_hierarchy_dedup']={k:dedup[k] for k in ('source_sha256','output_sha256','removed_exact_instances','all_39_macro_polygon_layers_XOR_equal_after_reopen','all_flattened_text_port_labels_identical')}
r['next_action']='Close actual short_cover_b signal geometry and require independent DRC plus all 41337 signal-net connectivity checks. Complete corrected full-GDS abstract-SRAM core LVS, then merge PG_D, repair antenna, and rerun all final same-version gates.'
for item in ['short_cover_a failed DRT-0206 on inherited open net3116; no final candidate accepted','short_bridges / short_paths / short_paths_fine found no accepted local changes; diagnostics only','pg_d_lvs_e completed diagnostic extraction but failed on original SRAM duplicate-instance import messages; rejected, not a passing LVS flow']:
    if item not in r['not_promoted']:r['not_promoted'].append(item)
snapshot=json.loads((C/'reports/short_b0_all_connectivity.json').read_text())
assert snapshot['all_signal_geometry_connected'] and snapshot['checked_multi_terminal_signal_clock_nets']==41337
r['subchecks']['short_b0_all_connectivity']={**snapshot,'final_acceptance':False,'scope':'Completed initial short_cover_b iteration snapshot only; inherited net3116 open repaired, but routing DRC remains and final geometry must be rechecked.'}
text=(C/'logs/short_cover_b.log').read_text(errors='replace');markers=re.findall(r'Completing \d+% with (\d+) violations',text)
r['current_router_partial_marker_count']=int(markers[-1]) if markers else None
r['subchecks']['core_LVS_flow_development']={'current_positive':'pg_d_core_lvs_b','current_negative':'pg_d_badpin_lvs_b','LVS_only_pin_interface_view':'reports/pg_d_core_lvs_view.json','unique_ports_required':125,'method_verified':False,'full_Magic_import_not_qualified':'SRAM mask-add/drop layers unsupported by normal Magic import; full manufacture GDS preserved. pg_d_lvs_f rejected.','rejected_positive_A_errors':1717,'rejected_positive_A_cause':'Pin geometry was present but macro port declarations were absent; positive/negative both rejected.','final_signal_candidate':False}
r['in_progress']=['Six-net repair short_cover_b: first completed snapshot has all 41337 nets geometrically connected, with ongoing routing violations','Core-LVS method: real 125-port pin interface plus LEF annotation, require positive zero and actual shifted-pin negative-control failure','Final common-candidate PG/antenna/electrical/fill/verification gates remain required']
cell=json.loads((C/'reports/device_feedback_pg_d_lvs_f/result.json').read_text());assert cell['all_two_positive_and_two_wiring_fault_controls_pass']
r['subchecks']['warning_bearing_cells']={'positive_cells':['decap_3','diode_2'],'two_positive_matches_and_two_wiring_fault_rejections':True,'evidence':'reports/device_feedback_pg_d_lvs_f/result.json','scope':'Actual individual standard cells from full-GDS diagnostic extraction; full core LVS still required.'}
for item in ['pg_d_lvs_f rejected: unsupported internal SRAM mask-add/drop/other layers; dedup preserves geometry but does not qualify this import','pg_d_core_lvs_a / badpin_a: 1717 LVS errors with absent macro port declarations; neither accepted']:
    if item not in r['not_promoted']:r['not_promoted'].append(item)
pg_native=json.loads((C/'reports/pg_d_independent.json').read_text())
assert pg_native['unresolved_count']==6 and all(m['type']=='Short' for m in pg_native['unresolved'])
r['subchecks']['PG_D'].update(complete_for_controlled_F_baseline=False,independent_net_aware_DRC=6,development_core_LVS_errors=38,requires_signal_rerouting_before_acceptance=True,IR_EM_screen_scope='Logical per-net controlled-load screen only. Six actual PG/signal shorts invalidate physical signoff until rerouted and all final checks repeated.')
r['subchecks']['PG_D']['evidence'].append('reports/pg_d_independent.json')
r['subchecks']['core_LVS_flow_development'].update(current_positive='baseline_core_lvs_a',current_negative='baseline_badpin_lvs_a',PG_D_positive_125_ports_LVS_errors=38,PG_D_shifted_pin_124_ports_LVS_errors=44,PG_D_six_power_signal_short_nets=['net117','net4040','net3083','net3323','net7524','net3415'])
r['in_progress']=['Six-net signal repair short_cover_b; first snapshot has all 41337 nets connected, router still optimizing violations','Core LVS method calibration on original F baseline; PG_D version has six independent native/LVS-confirmed power-signal shorts and is not accepted','Combine proven signal route with PG_D and native diode repair; clear all diode-affected nets plus the six PG-interaction nets before final routing','Final same-version DRC/LVS/antenna/STA/activity/IR/fill gates remain required']
item='PG_D: width/spacing KLayout DRC 0 and logical-load IR/EM screens pass, but six real PG/signal shorts were found by native DRC and 38 core LVS errors; no physical signoff acceptance'
if item not in r['not_promoted']:r['not_promoted'].append(item)
method=json.loads((C/'reports/core_lvs_method_verified.json').read_text())
assert method['validated_hierarchical_core_LVS_method'] and method['positive']['LVS_errors']==0 and method['intentional_pin_shift_negative_control']['LVS_errors']==44
r['subchecks']['core_LVS_flow_development'].update(method_verified=True,validated_baseline='baseline_core_lvs_a',baseline_LVS_errors=0,baseline_unique_declared_macro_ports=125,intentional_pin_shift_LVS_errors=44,evidence='reports/core_lvs_method_verified.json')
r['in_progress']=['Six-net signal repair short_cover_b; first snapshot has all 41337 nets connected, router still optimizing violations','Core LVS method calibrated: F baseline zero, shifted-pin control 44 errors; PG_D has six independent native/LVS-confirmed power-signal shorts and remains unaccepted','Combine closed signal route with PG_D and native diode repair; clear all diode nets plus the six PG-interaction nets before final routing','Final same-version DRC/LVS/antenna/STA/activity/IR/fill gates remain required']
signal=json.loads((C/'reports/short_b_final_independent.json').read_text())
connected=json.loads((C/'reports/short_b_final_all_connectivity.json').read_text())
signal_pair=json.loads((C/'runs/short_cover_b/1-openroad-detailedrouting/native_pair.json').read_text())
assert signal['odb_sha256']==connected['source_sha256']==signal_pair['odb_sha256']
assert signal['unresolved_count']==signal_pair['native_DRC']==4
assert connected['all_signal_geometry_connected'] and connected['checked_multi_terminal_signal_clock_nets']==41337
r['subchecks']['short_cover_b_final']={'source_sha256':signal['odb_sha256'],'independent_DRC':4,'raw_markers':signal['raw_marker_count'],'confirmed_partition_artifacts':signal['confirmed_partition_artifacts'],'antenna_nets':signal_pair['antenna_nets'],'all_41337_signal_clock_nets_geometrically_connected':True,'evidence':['reports/short_b_final_independent.json','reports/short_b_final_all_connectivity.json'],'final_acceptance':False}
r['route_latest_marker_count']=4
r['physical_candidate']='runs/short_cover_b (best checked source); runs/short_cover_c (active trial)'
r['next_action']='Close the four independently confirmed B signal shorts, then rebase PG_D, repair antenna and all six PG/signal shorts, and rerun the final same-version DRC, calibrated 125-port hierarchical core LVS, three-RC STA, activity/reset, controlled IR/EM and fill gates.'
r['in_progress']=['short_cover_c: both participants of all three remaining signal-crossing pairs rerouted from the connected B final, seed 19, 8 threads, 12 iterations; no acceptance before independent checks','B final: independent signal DRC 4, antenna 18, all 41337 signal/clock nets connected','PG_D remains unaccepted with six independently confirmed power/signal shorts; calibrated core LVS method is ready','Final same-version DRC/LVS/antenna/STA/activity/IR/fill gates remain required']
for name in ('final_jogs_a','final_crossings_a','final_paths_a','final_paths_b','background_restore_a'):
    path=C/'reports'/name/'result.json'
    if path.exists():
        item=f'{name}: diagnostic trial only; no final candidate accepted'
        if item not in r['not_promoted']:r['not_promoted'].append(item)
pg_e=json.loads((C/'reports/pg_e_independent.json').read_text())
pg_e_binding=json.loads((C/'reports/pg_e_geometry_binding.json').read_text())
assert pg_e['unresolved_count']==0 and pg_e['odb_sha256']==pg_e_binding['output_sha256']
r['subchecks']['PG_E']={'source_sha256':pg_e['odb_sha256'],'independent_net_aware_DRC':0,'five_compacted_or_relocated_eight_cut_arrays':True,'all_signal_wire_bytes_cells_graph_guides_obstructions_preserved':True,'full_GDS_core_LVS_and_controlled_IR_EM':'pending','accepted_for_final':False,'evidence':['reports/pg_compact_e/result.json','reports/pg_e_geometry_binding.json','reports/pg_e_independent.json']}
functional=json.loads((C/'functional/short_b/result.json').read_text())
coverage=json.loads((C/'functional/short_b/activity_coverage.json').read_text())
assert functional['all_reset_CDC_and_four_workloads_pass'] and len(coverage['runs'])==4
assert all(x['matched_routed_nets']==41337 and x['mapping_coverage_pct']==100 and not x['SRAM_input_unmapped'] and not x['SRAM_input_nets_with_unknown_time'] for x in coverage['runs'])
r['subchecks']['short_B_functional_activity']={'netlist_sha256':functional['netlist_sha256'],'reset_CDC_cycles':functional['reset_CDC']['cycles'],'reset_release_phases':8,'all_four_workloads_pass':True,'all_41337_nets_mapped_every_workload':True,'SRAM_input_unknown_or_unmapped':0,'mapped_net_unknown_time_fractions':{x['id']:x['mapped_unknown_time_fraction'] for x in coverage['runs']},'final_acceptance':False,'scope':'Actual B netlist. Zero-delay/no-SDF simulation; final selected netlist requires replay. Mapped-net X/Z is retained and is not a weighted Liberty pin-power unknown fraction.','evidence':['functional/short_b/result.json','functional/short_b/activity_coverage.json']}
r['in_progress']=['wide_polish_b: correct pinned INCR=3 initialization produced four real markers; larger NEARDRC repair windows are running','short_cover_c: both participants of remaining crossing pairs cleared; diagnostic retry still running, with no acceptance','PG_E independent full/context native DRC zero; full-GDS open DRC, calibrated core LVS and fresh controlled IR/EM remain','B netlist reset/CDC and all four workloads passed; all 41337 nets mapped; final same-version physical/electrical/fill gates remain']
r['next_action']='Finish signal closure using initialized large-window local routing; select PG_E only after fresh GDS/LVS/controlled IR/EM checks; merge and repair actual combined-candidate antenna/PG interaction nets, then rerun all final same-version gates.'
wide=json.loads((C/'reports/wide_b_independent.json').read_text());wide_cn=json.loads((C/'reports/wide_b_all_connectivity.json').read_text())
assert wide['unresolved_count']==3 and wide['odb_sha256']==wide_cn['source_sha256'] and wide_cn['all_signal_geometry_connected']
r['subchecks']['wide_B_checked']={'source_sha256':wide['odb_sha256'],'independent_DRC':3,'antenna_nets':18,'all_41337_signal_clock_nets_connected':True,'unresolved':[{k:m[k] for k in ('type','srcs','bbox_dbu','layer')} for m in wide['unresolved']],'final_acceptance':False,'evidence':['reports/wide_b_independent.json','reports/wide_b_all_connectivity.json']}
r['physical_candidate']='runs/wide_polish_b (best independently checked source); manual local geometry trials remain unaccepted'
r['route_latest_marker_count']=3
e_metrics=json.loads((C/'runs/pg_e_stream_a/2-klayout-drc/state_out.json').read_text())['metrics']
r['subchecks']['PG_E'].update(full_GDS_open_DRC=e_metrics['klayout__drc_error__count'],core_LVS='not run: nonzero GDS DRC input gate rejected',four_controlled_average_EM_cases_pass=True,accepted_for_final=False)
f=json.loads((C/'reports/pg_f_independent.json').read_text());fbind=json.loads((C/'reports/pg_f_geometry_binding.json').read_text())
assert f['unresolved_count']==0 and f['odb_sha256']==fbind['output_sha256']
r['subchecks']['PG_F']={'source_sha256':f['odb_sha256'],'independent_native_DRC':0,'three_0p22um_array_translations_from_E':True,'full_GDS_DRC_core_LVS_and_fresh_IR_EM':'pending','final_acceptance':False,'evidence':['reports/pg_f_geometry_binding.json','reports/pg_f_independent.json']}
r['in_progress']=['Best checked signal geometry: wide_polish_b independent DRC 3, antenna 18, all 41337 signal/clock nets connected','Same-net M1 patch removes one local marker in wide_notch_b; full/context recheck still required; bounded PG/signal detour trial running','PG_E rejected by three actual m5.2 GDS gaps despite native DRC 0 and four controlled EM passes; PG_F translates the three arrays by 0.22um and has independent native DRC 0; full GDS, core LVS and fresh IR/EM pending','Final same-version signal/PG/antenna/STA/GLS/activity/fill/model coverage gates remain required']
r['next_action']='Close actual remaining signal geometry, complete PG_F full-GDS/core-LVS/controlled-IR-EM checks, then rebase and measure the actual combined PG interactions and diode nets before fresh final common-candidate gates.'
selected_signal=json.loads((C/'reports/signal_selection.json').read_text())
signal_clean=json.loads((C/selected_signal['independent_report']).read_text());clean_conn=json.loads((C/selected_signal['connectivity_report']).read_text())
assert selected_signal['source_sha256']==signal_clean['odb_sha256']==clean_conn['source_sha256'] and signal_clean['unresolved_count']==0 and clean_conn['all_signal_geometry_connected']
r['subchecks']['selected_clean_signal']={**selected_signal,'all_41337_nets_connected':True,'exact_export_binding':'reports/manual_export51_binding.json' if selected_signal.get('driver_overlay') else 'reports/manual_export_binding.json','physical_scope':'Includes an explicit 3.05um LI1 underpass, a local M1 gap patch and a compact three-cut power row-feed stack. Fresh electrical and final common-candidate checks still required.'}
r['physical_candidate']='runs/'+selected_signal['run_tag']+' (independent native/context DRC 0 and all 41337 signal nets connected)'
r['route_latest_marker_count']=0
failed_lvs=json.loads((C/'runs/pg_f_core_lvs_a/2-netgen-lvs/state_out.json').read_text())['metrics']
assert failed_lvs['design__lvs_error__count']==29
r['subchecks']['PG_F'].update(full_GDS_open_DRC=0,four_controlled_average_EM_cases_pass=True,core_LVS_errors=29,physical_power_ground_contacts=2,final_acceptance=False,scope='Rejected: two actual M5 power/ground overlaps found by core LVS and explicit labeled-copper audit. Per-net native IR/EM and geometric DRC do not establish physical PG separation.')
g=json.loads((C/'reports/pg_g_independent.json').read_text());contacts=json.loads((C/'reports/pg_g_contacts.json').read_text());baseline_contacts=json.loads((C/'reports/pg_baseline_contacts.json').read_text())
assert g['unresolved_count']==0 and g['odb_sha256']==contacts['source_ODB_sha256'] and contacts['no_VPWR_VGND_copper_contact'] and baseline_contacts['no_VPWR_VGND_copper_contact']
r['subchecks']['PG_G']={'source_sha256':g['odb_sha256'],'independent_native_DRC':0,'explicit_power_ground_contact_audit':0,'baseline_zero_contact_control':True,'via4_array_replacements':181,'via4_cuts_at_planned_positions':1430,'three_cut_M1_M3_row_feed':True,'full_GDS_open_DRC':json.loads((C/'runs/pg_g_stream_a/2-klayout-drc/state_out.json').read_text())['metrics']['klayout__drc_error__count'],'core_LVS_and_fresh_controlled_IR_EM':'pending','final_acceptance':False,'evidence':['reports/pg_g_geometry_binding.json','reports/pg_g_independent.json','reports/pg_g_contacts.json','reports/pg_baseline_contacts.json']}
r['in_progress']=['Signal-only source selected: exact checked ODB exported with native/context DRC 0, all 41337 nets connected, antenna 18 still pending','Fresh three-RC electrical probe on the actual clean signal source, including explicit LI1 copper','PG_G native/context DRC 0, explicit PG contact audit 0, full GDS open DRC 0; core LVS, stream completeness and fresh controlled IR/EM in progress','Final common signal/PG/antenna/STA/GLS/activity/IR/fill gates remain required']
r['next_action']='Require PG_G actual core LVS zero plus full geometry/stream/contact/IR/EM evidence, then merge it onto the selected clean signal layout, measure actual combined interactions, insert/reconnect diodes and rerun all final common-candidate gates. Evaluate the fresh three-RC clean-signal probe before further physical ECOs.'
pg_selected=C/'reports/selected_pg.json'
if pg_selected.exists():
    pg=json.loads(pg_selected.read_text());assert pg['hierarchical_core_LVS_errors']==0
    r['subchecks']['PG_G'].update(pg,final_acceptance=False)
    r['in_progress']=['Selected 51-driver signal: independent native/context DRC 0, all 41337 nets connected, antenna 18; fresh three-RC electrical probe running','PG_G branch selected: native DRC, full-GDS open DRC, 125-port core LVS and PG contacts all 0; four controlled IR/EM cases pass','PG_G rebased onto actual 51-driver signal; common-candidate antenna/electrical/LVS/activity/IR/fill gates remain required']
    r['next_action']='Measure actual combined PG/signal geometry, repair antennas, then require every final common-candidate gate. The prior 50-driver clean-signal probe had max-RC slew/cap 11/1; the actual additional buffer change requires fresh RC/STA.'
probe=C/'reports/driver51_electrical_probe.json'
if probe.exists():
    r['subchecks']['driver51_electrical_probe']=json.loads(probe.read_text())
    r['subchecks']['actual_combined_PG_signal_DRC']=json.loads((C/'reports/focus_pg_independent.json').read_text())['unresolved_count']
    r['in_progress']=['51-driver exact clean-signal candidate: independent DRC 0, all 41337 nets connected; fresh three RC slew/cap/setup/hold violations 0','PG_G branch native/GDS/core-LVS/contact/IR-EM gates pass; rebased actual signal/PG native DRC also 0','Antenna insertion B uses verified reversible tap-name alias around the pinned inserter name-gap crash; final same-version antenna/electrical/LVS/activity/IR/fill gates remain required']
    r['next_action']='Complete actual diode insertion and reconnection, require independent DRC/all-net connectivity/antenna zero, then regenerate final filled GDS, three RC/STA, core LVS, functional/activity and final IR/EM/density evidence.'
(C/'WORK_STATE.json').write_text(json.dumps(r,indent=2)+'\n')
path=C.parent/'routing/WORK_STATE.json';data=json.loads(path.read_text(encoding='utf-8-sig'));data['follow_on_work'].update(status=r['status'],W25_complete=False,state='../week25_closure/WORK_STATE.json',updated_utc=r['updated_utc'],next_action=r['next_action']);path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Closure evidence updated',r['updated_utc'],'route markers',r['route_latest_marker_count'])
