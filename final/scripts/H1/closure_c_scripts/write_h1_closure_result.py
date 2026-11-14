"""Judge every H1 W25-method closure gate from its report and write reports/H1_closure_result.json (host python)."""
import datetime, hashlib, json, re
from pathlib import Path
CB = Path(__file__).resolve().parents[1]
H = CB.parent
R = CB / 'reports'
def j(n): return json.loads((R / n).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ir(tag):
    t = (CB / 'logs' / (tag + '.log')).read_text(errors='replace')
    v = [float(x) for x in re.findall(r'Worstcase IR drop:\s*([0-9.e+-]+) V', t)]
    assert len(v) == 2, tag
    return {'VPWR_worst_mV': round(v[0] * 1e3, 2), 'VGND_worst_mV': round(v[1] * 1e3, 2), 'combined_mV': round(sum(v) * 1e3, 2)}

drc = j('h1_filled_independent.json'); conn = j('h1_filled_all_connectivity.json'); macro = j('h1_macro_audit.json')
std = j('h1_stdcell_audit.json'); pgc = j('h1_pg_contacts.json'); em = j('h1_em_resistor_audit.json')
fomr = j('h1_fom_repair.json'); lir = j('h1_li_repair.json'); dens = j('h1_sliding_density.json')
grid = j('h1_dummy_grid.json'); fom = j('h1_fom_geometry.json')
rdb = (R / 'h1_fill_beol.rdb').read_text(errors='replace')
odb = H / 'runs/h1c_post/1-openroad-fillinsertion/fault_v_asic_top.odb'
gds = H / 'runs/h1c_post/2-klayout-streamout/fault_v_asic_top.gds'
filled = CB / 'final_fill/filled.gds.gz'
chain = (CB / 'logs/chain.log').read_text()
gates = {
    'chain_all_rc_0': bool(re.search(r'CLOSURE_END pdn=0 drc=0 conn=0 vias=0 pgg=0 stream=0 final_ir_0p014_h1=0 final_ir_0p028_h1=0 em=0 fillgen=0 fillchk=0 beol=0', chain)),
    'native_full_chip_DRC_unresolved_0': drc['unresolved_count'] == 0 and drc['raw_marker_count'] == drc['confirmed_partition_artifacts'],
    'all_signal_nets_connected': conn['all_signal_geometry_connected'] and not conn['bad_nets'] and not conn['missing_wires'],
    'SRAM_macro_layers_exact': macro['all_selected_manufacturing_layers_exact'] and macro['referenced_macro_instances'] == {'sky130_sram_2kbyte_1rw1r_32x512_8': 18},
    'stdcell_and_via_stream_match': std['all_component_counts_match_fresh_DEF'] and std['all_used_standard_cell_polygon_layers_match_library'] and std['all_route_via_counts_and_geometry_match_native_ODB'] and std['shifted_polygon_negative_control_detected'],
    'no_VPWR_VGND_contact': pgc['no_VPWR_VGND_copper_contact'] and not pgc['positive_area_PG_contacts'],
    'PG_average_EM_pass': em['native_average_current_screen_pass'] and not em['violations'],
    'fill_FOM_LI_repairs_clean': fomr['all_other_seven_fill_layers_XOR_empty'] and fomr['width_spacing_implant_screens_pass'] and lir['native_li8_markers_after'] == 0 and lir['full_LI_dummy_minimum_width_screen_pass'],
    'sliding_density_actual_die_pass': dens['all_numeric_density_checks_pass'] and dens['die_um'] == [2470.0, 3217.0],
    'dummy_grid_pass': grid['screen_pass'] and grid['positive_and_negative_controls_pass'],
    'FOM_geometry_pass': fom['screen_pass'] and fom['negative_control_detected'] and not any(fom['global_checks'].values()),
    'fill_BEOL_interaction_markers_0': rdb.count('<item>') == 0 and rdb.count('<category>') > 50,
}
gates['ODB_binding_consistent'] = drc['odb_sha256'] == conn['source_sha256'] == pgc['source_ODB_sha256'] == sha(odb)
gates['GDS_binding_consistent'] = std['stream_GDS_sha256'] == fomr['source_geometry_sha256'] == dens['base_sha256'] == fom['source_sha256'] == sha(gds)
result = {
    'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'design': 'H1 cand_gap90x95 (h1c_pg_r1 -> h1c_post)',
    'method': 'H0 week25_closure gate scripts with path patches (reports/script_provenance.json); density re-run over the actual H1 die (scripts/check_sliding_density_die.py) after the first run used the H0 die extent 2500x3300um (kept as reports/h1_sliding_density_H0die_misscoped.json)',
    'all_W25_method_gates_pass': all(gates.values()),
    'gates': gates,
    'numbers': {
        'native_DRC_raw_markers': drc['raw_marker_count'], 'native_DRC_partition_artifacts': drc['confirmed_partition_artifacts'],
        'connected_signal_nets': conn['checked_multi_terminal_signal_clock_nets'], 'diode_terminals': conn['diode_terminals'],
        'stdcell_instances': std['standard_cell_instances'], 'stdcell_masters': std['used_standard_cell_masters'], 'route_vias': std['routing_via_instances'],
        'IR_14mW_per_SRAM': ir('final_ir_0p014_h1'), 'IR_28mW_per_SRAM': ir('final_ir_0p028_h1'),
        'EM_worst_ratio': {c: {n: round(max(b['utilization'] for b in v['worst_per_layer'].values()), 3) for n, v in em['cases'][c].items()} for c in em['cases']},
        'density_window_min_max': {L: [round(v['window_min'], 3), round(v['window_max'], 3), v['limits']] for L, v in dens['layers'].items()},
        'density_windows_per_layer': dens['windows_per_layer'],
        'removed_FOM_dummy_islands': fomr['removed_FOM_islands'], 'removed_LI_dummy_islands': lir['removed_LI_dummy_islands'],
    },
    'filled_ODB_sha256': sha(odb), 'core_GDS_sha256': sha(gds), 'dummy_filled_GDS_sha256': sha(filled),
    'fill_pattern_sha256': dens['fill_sha256'],
    'report_sha256': {p.name: sha(p) for p in sorted(R.glob('h1_*.json')) if p.stat().st_size < 3_000_000} | {'h1_fill_beol.rdb': sha(R / 'h1_fill_beol.rdb')},
    'not_covered_same_as_H0': 'foundry/SRAM-interior signoff, fill-aware PEX, multi-PVT SRAM models, transient/package IR, current crowding, DFT/pad/ESD hardware, silicon',
}
(R / 'H1_closure_result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'all': result['all_W25_method_gates_pass'], 'gates': gates, 'em': result['numbers']['EM_worst_ratio'], 'ir': [result['numbers']['IR_14mW_per_SRAM'], result['numbers']['IR_28mW_per_SRAM']], 'dens': result['numbers']['density_window_min_max']}, indent=1))
