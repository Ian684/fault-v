"""Create the H1 W25-closure workspace (host python3, run once). Copies the W25 closure gate scripts (read only source)
into closure_c/scripts, re-pointing only their output/working directory and PDK/routing roots; check logic is unchanged.
Also writes the H1 IR config/state/Tcl bound by SHA256 to the H1 signoff ODB, nominal SPEF and mixed VCD."""
from pathlib import Path
import hashlib, json, re, shutil

CB = Path(__file__).resolve().parent                     # .../ppa/h1/cand_gap90x95/closure_c
CAND = CB.parent
ROOT = CAND.parents[2]                                   # fault-v-asic
W25 = ROOT / 'week25_closure'
WCB = '/work/ppa/h1/cand_gap90x95/closure_c'
for d in ('scripts', 'reports', 'logs', 'controls', 'runs'):
    (CB / d).mkdir(exist_ok=True)


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


verbatim = ['export_native_vias.py', 'export_pg_contact_geometry.py', 'audit_pg_contacts.py', 'run_native_fill.py',
            'repair_fom_fill.py', 'repair_li_fill.py', 'check_sliding_density.py', 'canonicalize_fill.py',
            'compose_fill.py', 'check_full_fom.py']
patched = {
    'audit_stream_macro.py': [("C=Path('/work/week25_closure')", f"C=Path('{WCB}')")],
    'audit_final_stdcell_stream.py': [("C=Path('/work/week25_closure');library=C.parent/'pdk", f"C=Path('{WCB}');library=Path('/work')/'pdk")],
    'audit_all_signal_connectivity.py': [("C=Path('/work/week25_closure');R=C.parent/'routing'", f"C=Path('{WCB}');R=Path('/work/routing')")],
    'check_dummy_grid.py': [("C=Path('/work/week25_closure')", f"C=Path('{WCB}')"), ("tlef=C.parent/'pdk", "tlef=Path('/work')/'pdk")],
    # truncation guard: H0 (with its PG_G via arrays) exports ~335k PG resistors, H1 (smaller die) ~267k per net;
    # completeness is still required by reaching the '* Sinks' marker and by every EM row joining a resistor.
    'audit_pg_em.py': [("tlef=C.parent/'pdk", "tlef=Path('/work')/'pdk"),
                       ("total_resistors>300000", "total_resistors>200000")],
}
provenance = {}
for name in verbatim + list(patched):
    src = W25 / 'scripts' / name
    text = src.read_text()
    for old, new in patched.get(name, []):
        assert text.count(old) == 1, (name, old)
        text = text.replace(old, new)
    dst = CB / 'scripts' / name
    dst.write_text(text)
    provenance[name] = {'source': str(src.relative_to(ROOT)), 'source_sha256': sha(src), 'copy_sha256': sha(dst),
                        'path_patches': [n for _, n in patched.get(name, [])]}

# ---- IR inputs (same method as week25_closure/scripts/prepare_final_ir.py, H1 files) ----
odb_path = CAND / 'runs/h1c_post/1-openroad-fillinsertion/fault_v_asic_top.odb'
activity = json.loads((CAND / 'functional/h1c_a/result.json').read_text())
targets = json.loads((CAND / 'functional/h1c_a/activity_targets.json').read_text())
assert activity['all_reset_CDC_and_four_workloads_pass']
odb_sha = sha(odb_path)
assert targets['candidate_ODB_sha256'] == odb_sha
vcd = CAND / 'functional/h1c_a/mixed/activity.vcd'
mixed = next(r for r in activity['activity_runs'] if r['id'] == 'mixed')
assert sha(vcd) == mixed['sha256']
state = json.loads((CAND / 'runs/h1c_post/5-openroad-rcx/state_out.json').read_text())
assert state['odb'].endswith('/h1c_post/1-openroad-fillinsertion/fault_v_asic_top.odb')
assert sha(ROOT / Path(state['nl']).relative_to('/work')) == activity['netlist_sha256']
state.update(spef={'nom_*': state['spef']['nom_*']}, metrics={}, sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('gds', 'klayout_gds'):
    state.pop(key, None)
spef_sha = sha(ROOT / Path(state['spef']['nom_*']).relative_to('/work'))
cfg = json.loads((W25 / 'config_pg_ir.json').read_text())
placement = {}
for line in (CAND / 'runs/h1_floorplan/07-odb-manualmacroplacement/placement.cfg').read_text().split('\n'):
    if line.strip():
        inst, x, y, orient = line.split()
        placement[inst] = {'location': [float(x), float(y)], 'orientation': orient}
assert set(placement) == set(cfg['MACROS']['sky130_sram_2kbyte_1rw1r_32x512_8']['instances'])
cfg['MACROS']['sky130_sram_2kbyte_1rw1r_32x512_8']['instances'] = placement
cfg['VSRC_LOC_FILES'] = {'VPWR': f'{WCB}/controls/VPWR.loc', 'VGND': f'{WCB}/controls/VGND.loc'}
(CB / 'config_h1_ir.json').write_text(json.dumps(cfg, indent=2) + '\n')
(CB / 'h1_ir_state.json').write_text(json.dumps(state, indent=2) + '\n')
code = (W25 / 'controls/pg_ir_native.tcl').read_text()
vcd_w = '/work/' + str(vcd.relative_to(ROOT))
assert code.count('/runtime/mixed.activity.vcd') == 1
code = code.replace('/runtime/mixed.activity.vcd', vcd_w)
guards = '\n'.join(f'if {{[lindex [exec sha256sum {p}] 0] ne "{d}"}} {{error "Final IR input hash mismatch: {k}"}}'
                   for k, p, d in [('ODB', '$::env(CURRENT_ODB)', odb_sha), ('SPEF', '$::env(CURRENT_SPEF_DEFAULT_CORNER)', spef_sha),
                                   ('VCD', vcd_w, mixed['sha256'])]) + '\n'
assert code.count('read_current_odb\n') == 1
code = code.replace('read_current_odb\n', 'read_current_odb\n' + guards + 'puts "W25_FINAL_IR_INPUT_HASHES_VERIFIED"\n')
(CB / 'controls/h1_ir_native.tcl').write_text(code)
(CB / 'scripts/h1_ir_cli.py').write_text(
    "import runpy\nfrom librelane.steps import Step\n"
    f"Step.factory.get('OpenROAD.IRDropReport').get_script_path=lambda self:'{WCB}/controls/h1_ir_native.tcl'\n"
    "runpy.run_module('librelane',run_name='__main__')\n")
(CB / 'reports/runtime_h1_filled_odb.json').write_text(json.dumps(
    {'source': '/work/' + str(odb_path.relative_to(ROOT)), 'sha256': odb_sha, 'bytes': odb_path.stat().st_size}, indent=2) + '\n')
core_gds = CAND / 'runs/h1c_post/2-klayout-streamout/fault_v_asic_top.gds'
(CB / 'reports/runtime_h1_core_gds.json').write_text(json.dumps(
    {'source': '/work/' + str(core_gds.relative_to(ROOT)), 'sha256': sha(core_gds), 'bytes': core_gds.stat().st_size}, indent=2) + '\n')
(CB / 'reports/h1_ir_input.json').write_text(json.dumps(
    {'ODB_sha256': odb_sha, 'netlist_sha256': activity['netlist_sha256'], 'mixed_VCD_sha256': mixed['sha256'],
     'nominal_SPEF_sha256': spef_sha, 'macro_budgets_W_each': [0.014, 0.028],
     'method': 'week25_closure prepare_final_ir.py / pg_ir_native.tcl with H1 files; VSRC: existing met5 PG terminals within 100 um of the H1 die edge (week25_signoff inspect_pdn.py rule)'}, indent=2) + '\n')
(CB / 'reports/script_provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
print('CLOSURE_B_SETUP_DONE', len(provenance), odb_sha, spef_sha, mixed['sha256'])
