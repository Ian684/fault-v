"""Build the H1 formal PPA result and the H0/H1 comparison (H0 method: ppa/formal_h0/scripts/summarize_h0.py).

Reads only: the H1 power log, H1 run metrics (h1c_post, h1c_sta, h1c_lvs, h1c_lvs_bad), the H1 functional/activity
receipts and ppa/formal_h0/reports/H0_PPA_result.json. Writes ppa/formal_h1/reports/H1_PPA_result.json and
H0_H1_comparison.json. Check results are recorded as found; nothing is forced to pass.
"""
from pathlib import Path
import hashlib, json, re

root = Path(__file__).resolve().parents[3]
h1 = root / 'ppa' / 'formal_h1'
cand = root / 'ppa' / 'h1' / 'cand_gap90x95'
runs = cand / 'runs'
period_ns = 40.0


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


log = (h1 / 'logs' / 'power_h1c.log').read_text()
assert (h1 / 'logs' / 'power_h1c.exit').read_text().strip() == '0' and 'FAULTV_POWER_COMPLETED' in log
post_in = read(cand / 'signoff/reports_c/post_input.json')
area = read(runs / 'h1c_post/final/metrics.json')
timing = read(runs / 'h1c_sta/final/metrics.json')
lvs = read(runs / 'h1c_lvs/final/metrics.json')
bad = read(runs / 'h1c_lvs_bad/final/metrics.json')
activity = read(cand / 'functional/h1c_a/result.json')
coverage = read(cand / 'functional/h1c_a/activity_coverage.json')
targets = read(cand / 'functional/h1c_a/activity_targets.json')
h0 = read(root / 'ppa/formal_h0/reports/H0_PPA_result.json')

netlist = runs / 'h1c_post/final/nl/fault_v_asic_top.nl.v'
spef = runs / 'h1c_post/final/spef/nom/fault_v_asic_top.nom.spef'
filled_odb = next(runs.glob('h1c_post/*-openroad-fillinsertion/fault_v_asic_top.odb'))
# one candidate everywhere: functional + activity ran on this netlist / filled ODB, power on this netlist + SPEF
assert activity['netlist_sha256'] == coverage['netlist_sha256'] == targets['candidate_netlist_sha256'] == sha(netlist)
assert targets['candidate_ODB_sha256'] == sha(filled_odb)
assert sha(runs / post_in['final_eco_run'] / '01-openroad-detailedrouting/eco_final.odb') == post_in['routed_odb_sha256']

# ---- power (same parsing and self-checks as H0) ----
aruns = {r['id']: r for r in activity['activity_runs']}
power = {}
for case, body in re.findall(r'FAULTV_CASE_BEGIN (\S+)\n(.*?)FAULTV_CASE_END \1', log, re.S):
    assert re.search(r'unannotated\s+0\b', body), case
    groups = {g: [float(x) for x in v.split()] for g, v in re.findall(
        r'^(Sequential|Combinational|Clock|Macro|Pad|Total)\s+(\S+\s+\S+\s+\S+\s+\S+)', body, re.M)}
    srams = [float(x) for x in re.findall(r'^\s*\S+\s+\S+\s+\S+\s+(\S+) u_soc\.\S+u_sram$', body, re.M)]
    assert len(srams) == 18 and abs(sum(srams) - groups['Macro'][3]) < 1e-6, case
    run = aruns[case]
    window_us = run['cycles'] * period_ns / 1000
    assert abs((run['end_ns'] - run['start_ns']) / 1000 - window_us) < 1e-9, case
    total_mW = groups['Total'][3] * 1e3
    macro_mW = groups['Macro'][3] * 1e3
    power[case] = {
        'cycles': run['cycles'], 'window_us': window_us, 'vcd_sha256': run['sha256'],
        'group_total_mW': {g: v[3] * 1e3 for g, v in groups.items()},
        'internal_switching_leakage_mW': [x * 1e3 for x in groups['Total'][:3]],
        'total_mW': total_mW, 'logic_mW': total_mW - macro_mW, 'sram_mW': macro_mW,
        'sram_per_bank_mW': sorted(set(round(x * 1e3, 9) for x in srams)),
        'energy_nJ': total_mW * window_us, 'logic_energy_nJ': (total_mW - macro_mW) * window_us,
        'energy_per_cycle_pJ': total_mW * period_ns,
    }
assert set(power) == set(h0['power']) == set(aruns)
annotated = sorted({int(x) for x in re.findall(r'^Annotated (\d+) pin activities\.', log, re.M)})
assert annotated == [137242], annotated

dot_r, dot_c = power['dot64_rv32i'], power['dot64_custom']
fmax = {c.split(':')[1]: {'setup_ws_ns': timing[c], 'min_period_ns': period_ns - timing[c],
                          'fmax_MHz': 1000 / (period_ns - timing[c])}
        for c in timing if c.startswith('timing__setup__ws__corner:')}
hold = {c.split(':')[1]: timing[c] for c in timing if c.startswith('timing__hold__ws__corner:')}
assert len(fmax) == len(hold) == 3

# ---- checks, recorded as found ----
sta_counts = {k: v for k, v in timing.items() if k.endswith('__count') or '__count__corner:' in k}
lvs_counts = {k: v for k, v in lvs.items() if k.startswith('design__lvs_') or k.startswith('magic__')}
checks = {
    'native_router': {'DRC': post_in['native_DRC'], 'antenna_nets': post_in['native_antenna_nets'],
                      'final_eco_run': post_in['final_eco_run'], 'routed_odb_sha256': post_in['routed_odb_sha256']},
    'klayout_drc_error_count': area['klayout__drc_error__count'],
    'antenna_violating_nets': area['antenna__violating__nets'],
    'antenna_violating_pins': area['antenna__violating__pins'],
    'sta_violation_counts_nonzero': {k: v for k, v in sta_counts.items() if v != 0},
    'sta_violation_count_metrics_checked': len(sta_counts),
    'sta_min_setup_ws_ns': min(v['setup_ws_ns'] for v in fmax.values()),
    'sta_min_hold_ws_ns': min(hold.values()),
    'core_lvs': lvs_counts,
    'core_lvs_negative_control_errors': bad['design__lvs_error__count'],
    'reset_CDC': activity['reset_CDC'],
    'four_workloads_pass': activity['all_reset_CDC_and_four_workloads_pass'],
    'activity_mapping_coverage_pct': sorted({r['mapping_coverage_pct'] for r in coverage['runs']}),
    'routed_signal_clock_nets': len(targets['routed_signal_clock_nets']),
    'power_annotated_pins': annotated,
}
passes = {
    'native_router_clean': post_in['native_DRC'] == 0 and post_in['native_antenna_nets'] == 0,
    'klayout_drc_clean': area['klayout__drc_error__count'] == 0,
    'antenna_clean': area['antenna__violating__nets'] == 0 and area['antenna__violating__pins'] == 0,
    'sta_clean': len(sta_counts) >= 28 and not checks['sta_violation_counts_nonzero']
                 and checks['sta_min_setup_ws_ns'] > 0 and checks['sta_min_hold_ws_ns'] > 0,
    'core_lvs_clean': len(lvs_counts) == 8 and all(v == 0 for v in lvs_counts.values()),
    'core_lvs_negative_control_detected': bad['design__lvs_error__count'] > 0,
    'functional_pass': bool(activity['all_reset_CDC_and_four_workloads_pass']),
    'activity_fully_mapped': checks['activity_mapping_coverage_pct'] == [100.0],
}
all_pass = all(passes.values())

result = {
    'phase': 'H1 formal PPA (die-shrink implementation of the H0 mapped netlist)',
    'all_h1_checks_pass': all_pass, 'passes': passes, 'checks': checks,
    'not_done_for_h1': ['DFT / pad / ESD review (design-level, shared with H0)'],
    'W25_method_closure': (lambda c: {'result': 'ppa/h1/cand_gap90x95/closure_c/reports/H1_closure_result.json',
                                      'all_W25_method_gates_pass': c['all_W25_method_gates_pass'],
                                      'filled_ODB_matches': c['filled_ODB_sha256'] == sha(filled_odb),
                                      'IR_EM': {k: c['numbers'][k] for k in ('IR_14mW_per_SRAM', 'IR_28mW_per_SRAM', 'EM_worst_ratio')},
                                      'dummy_filled_GDS_sha256': c['dummy_filled_GDS_sha256']})(
        json.loads((root / 'ppa/h1/cand_gap90x95/closure_c/reports/H1_closure_result.json').read_text())),
    'candidate': {'netlist_sha256': sha(netlist), 'nom_SPEF_sha256': sha(spef),
                  'SDC_sha256': sha(root / 'week25_signoff/constraints_reviewed.sdc'),
                  'filled_ODB_sha256': sha(filled_odb), 'routed_ODB_sha256': post_in['routed_odb_sha256']},
    'conditions': {'PVT': 'TT 25C 1.8V', 'RC_power': 'nom', 'clock_MHz': 1000 / period_ns},
    'area_um2': {k.replace('design__', ''): v for k, v in area.items() if 'area' in k},
    'instance_counts': {k.replace('design__instance__count__', ''): v for k, v in area.items() if k.startswith('design__instance__count')},
    'utilization': {'all_instances': area['design__instance__utilization'], 'stdcell': area['design__instance__utilization__stdcell']},
    'timing': {'setup_ws_ns': {k: v['setup_ws_ns'] for k, v in fmax.items()}, 'hold_ws_ns': hold,
               'slack_based_fmax_estimate': fmax},
    'power': power,
    'dot64': {'mac_count': 64, 'result': 60256,
              'cycle_ratio_rv32i_over_custom': dot_r['cycles'] / dot_c['cycles'],
              'energy_ratio_rv32i_over_custom': dot_r['energy_nJ'] / dot_c['energy_nJ'],
              'energy_per_MAC_nJ': {'rv32i': dot_r['energy_nJ'] / 64, 'custom': dot_c['energy_nJ'] / 64}},
    'unknown_time_fraction': {r['id']: r['mapped_unknown_time_fraction'] for r in coverage['runs']},
    'toggling_routed_nets': {r['id']: r['toggling_routed_nets'] for r in coverage['runs']},
}


# ---- H0 / H1 comparison ----
def row(a, b):
    return {'H0': a, 'H1': b, 'delta': b - a, 'delta_pct': (100 * (b - a) / a) if a else None}


def both(path):
    x, y = h0, result
    for key in path:
        x, y = x[key], y[key]
    return row(x, y)


cmp = {'all_h1_checks_pass': all_pass,
       'same_cycles_all_workloads': all(h0['power'][c]['cycles'] == power[c]['cycles'] for c in power),
       'area_um2': {k: both(('area_um2', k)) for k in h0['area_um2'] if k in result['area_um2']},
       'instance_counts': {k: both(('instance_counts', k)) for k in h0['instance_counts'] if k in result['instance_counts']},
       'utilization': {k: both(('utilization', k)) for k in h0['utilization']},
       'setup_ws_ns': {k: both(('timing', 'setup_ws_ns', k)) for k in h0['timing']['setup_ws_ns']},
       'hold_ws_ns': {k: both(('timing', 'hold_ws_ns', k)) for k in h0['timing']['hold_ws_ns']},
       'fmax_MHz': {k: both(('timing', 'slack_based_fmax_estimate', k, 'fmax_MHz')) for k in h0['timing']['setup_ws_ns']},
       'power_mW': {c: {'total': both(('power', c, 'total_mW')), 'logic': both(('power', c, 'logic_mW')),
                        'sram': both(('power', c, 'sram_mW')),
                        **{g: both(('power', c, 'group_total_mW', g)) for g in ('Sequential', 'Combinational', 'Clock')},
                        'switching': row(h0['power'][c]['internal_switching_leakage_mW'][1], power[c]['internal_switching_leakage_mW'][1])}
                    for c in power},
       'energy_nJ': {c: both(('power', c, 'energy_nJ')) for c in power},
       'logic_energy_nJ': {c: both(('power', c, 'logic_energy_nJ')) for c in power},
       'dot64_energy_ratio': both(('dot64', 'energy_ratio_rv32i_over_custom'))}
assert cmp['same_cycles_all_workloads']

(h1 / 'reports').mkdir(exist_ok=True)
(h1 / 'reports' / 'H1_PPA_result.json').write_text(json.dumps(result, indent=2) + '\n')
(h1 / 'reports' / 'H0_H1_comparison.json').write_text(json.dumps(cmp, indent=2) + '\n')
print('ALL_H1_CHECKS_PASS', all_pass)
print(json.dumps(passes, indent=1))
print(json.dumps(checks, indent=1))
short = lambda r: {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}
for sect in ('area_um2', 'instance_counts', 'utilization', 'setup_ws_ns', 'hold_ws_ns', 'fmax_MHz', 'energy_nJ', 'logic_energy_nJ'):
    print(sect)
    for k, r in cmp[sect].items():
        print('  ', k, short(r))
print('power_mW')
for c, rows in cmp['power_mW'].items():
    for k, r in rows.items():
        print('  ', c, k, short(r))
print('dot64', json.dumps(result['dot64']))
print('unknown', result['unknown_time_fraction'], result['toggling_routed_nets'])
