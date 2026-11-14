"""Verify actual core LVS/stream/connectivity/activity results before expensive final screens."""
from pathlib import Path
import hashlib,json,re
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads((C/p).read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def local(p):return C/Path(p).relative_to('/work/week25_closure')
for name in ('final_core_lvs','final_stream_audits','final_functional'):
    assert (C/'logs'/(name+'.exit')).read_text().strip()=='0',name
post=read('reports/final_post_verified.json');stage=read('reports/runtime_final_filled_odb.json');gdsstage=read('reports/runtime_final_core_gds.json')
digest=stage['sha256'];assert digest==post['filled_ODB_sha256'] and gdsstage['sha256']==post['full_geometry_core_GDS_sha256']
dr=read('reports/final_filled_independent.json');cn=read('reports/final_filled_all_connectivity.json')
assert digest==dr['odb_sha256']==cn['source_sha256'] and dr['unresolved_count']==0 and dr['physical_geometry_unchanged']
assert cn['checked_multi_terminal_signal_clock_nets']==41337 and cn['all_signal_geometry_connected'] and not cn['bad_nets'] and not cn['missing_wires']
macro=read('reports/final_macro_audit.json');std=read('reports/final_stdcell_audit.json');via=read('reports/final_native_vias.json')
assert macro['all_selected_manufacturing_layers_exact'] and all(len(v)==39 for v in macro['masters'].values()) and sum(macro['referenced_macro_instances'].values())==18
assert sha(local(macro['core_gds']))==gdsstage['sha256']==std['stream_GDS_sha256'] and via['source_ODB_sha256']==digest
assert std['all_component_counts_match_fresh_DEF'] and std['all_used_standard_cell_polygon_layers_match_library'] and std['all_route_via_counts_and_geometry_match_native_ODB'] and std['shifted_polygon_negative_control_detected']
pg=read('reports/final_pg_contacts.json');assert pg['source_ODB_sha256']==digest and pg['no_VPWR_VGND_copper_contact'] and not pg['positive_area_PG_contacts']
view=read('reports/final_core_lvs_view.json');assert view['manufacturing_source_GDS_sha256']==gdsstage['sha256'] and view['unique_SRAM_ports']==125 and view['SRAM_instances']==18
assert view['all_LEF_pin_rectangles_inside_actual_full_GDS_metal'] and view['all_actual_pin_labels_inside_matching_interfaces'] and view['chip_routing_standard_cell_geometry_labels_and_top_instances_unchanged']
assert sha(C/'inputs/final_core_lvs.gds')==view['LVS_only_view_sha256']
run=C/'runs/final_core_lvs_a';manifest=read('runs/final_core_lvs_a/native_archive_manifest.json');assert manifest['all_byte_exact']
for name,row in manifest['files'].items():
    p=run/name;assert p.resolve().is_relative_to(run.resolve()) and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],str(p)
lvs=read('runs/final_core_lvs_a/2-netgen-lvs/state_out.json');m=lvs['metrics']
assert m['magic__illegal_overlap__count']==0 and all(v==0 for k,v in m.items() if k.startswith('design__lvs_')),m
assert sha(local(lvs['pnl']))==sha(C/'runs/focus_post_b/1-openroad-fillinsertion/fault_v_asic_top.pnl.v')
ext=(run/'1-magic-spiceextraction/extraction/sky130_sram_2kbyte_1rw1r_32x512_8.ext').read_text()
ports=re.findall(r'^port "([^"\n]+)"\s+(\d+)\s',ext,re.M)
assert {n for n,i in ports}==set(view['pin_names']) and len({i for n,i in ports})==125
cal=read('reports/core_lvs_method_verified.json');assert cal['validated_hierarchical_core_LVS_method'] and cal['intentional_pin_shift_negative_control']['LVS_errors']==44
function=read('functional/final_a/result.json');coverage=read('functional/final_a/activity_coverage.json');targets=read('functional/final_a/activity_targets.json')
assert function['all_reset_CDC_and_four_workloads_pass'] and function['reset_CDC']['cycles']==97 and function['reset_CDC']['release_phases']==8
assert post['fresh_netlist_sha256']==function['netlist_sha256']==coverage['netlist_sha256']==targets['candidate_netlist_sha256'] and targets['candidate_ODB_sha256']==digest
assert coverage['parser_selfcheck_passed'] and len(coverage['runs'])==len(function['activity_runs'])==4
assert {r['id'] for r in coverage['runs']}=={'idle','mixed','dot64_rv32i','dot64_custom'}
activity={}
for r in coverage['runs']:
    run=next(v for v in function['activity_runs'] if v['id']==r['id']);assert run['passed'] and sha(local(run['vcd']))==run['sha256']==r['source_sha256']
    assert r['expected_routed_nets']==r['matched_routed_nets']==41337 and r['mapping_coverage_pct']==100 and not r['unmapped_routed_nets']
    assert not r['SRAM_input_unmapped'] and not r['SRAM_input_nets_with_unknown_time']
    activity[r['id']]={k:r[k] for k in ('cycles','mapping_coverage_pct','mapped_unknown_time_fraction','clock_edges','toggling_routed_nets')}
record={'filled_ODB_sha256':digest,'manufacturing_core_GDS_sha256':gdsstage['sha256'],'fresh_netlist_sha256':post['fresh_netlist_sha256'],'filled_native_context_DRC':0,'all_41337_signal_clock_nets_geometrically_connected':True,'diode_terminals':cn['diode_terminals'],'core_LVS_errors':0,'unique_declared_SRAM_ports':125,'SRAM_interfaces':18,'macro_39_layer_geometry_and_all_used_stdcell_and_via_stream_audits_pass':True,'no_VPWR_VGND_copper_contacts':True,'reset_CDC_cycles':97,'reset_release_phases':8,'four_workloads_pass':True,'activity':activity,'all_W25_gates_complete':False,'scope':'Actual common-candidate core/pin-interface LVS and physical/digital screens. SRAM interior is opaque; X/Z activity time is retained explicitly. No SDF, analog CDC/MTBF, recovery/removal, foundry or SRAM qualification inferred. Final IR/EM/fill and comprehensive completion gate remain required.'}
p=C/'reports/final_core_verified.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n');print('FINAL_CORE_LVS_STREAM_CONNECTIVITY_FUNCTIONAL_ACTIVITY_VERIFIED',digest,flush=True)
