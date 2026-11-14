"""Assemble the W26 delivery package (H0 + H1) from frozen sources, verifying every copy by SHA256.
Usage (WSL python3, from anywhere):
  build_delivery.py copy       copy sources into w26/delivery/Fault-V_W26 (refuses to overwrite)
  build_delivery.py finalize   write SHA256SUMS + manifest.json (after OASIS/XOR steps)
  build_delivery.py zip        write w26/delivery/Fault-V_W26.zip and verify every member against SHA256SUMS
Sources are only read; nothing under week25_closure / week25_signoff is written."""
import hashlib, json, shutil, sys, time, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # .../fault-v-asic
W26 = ROOT / 'w26'
PKG = W26 / 'delivery' / 'Fault-V_W26'
ZIP = W26 / 'delivery' / 'Fault-V_W26.zip'
H0R = 'week25_closure/runs/focus_post_b/final'
H1 = 'ppa/h1/cand_gap90x95'
H1R = H1 + '/runs/h1c_post/final'
SDC = 'week25_signoff/constraints_reviewed.sdc'

# (package path, source path, expected sha256 prefix or None)
FILES = [
    # ---------------- H0 (W25 final candidate) ----------------
    ('H0/layout/fault_v_asic_top.gds', H0R + '/gds/fault_v_asic_top.gds', '67bcff91'),
    ('H0/layout/fault_v_asic_top_filled.gds.gz', 'week25_closure/final_fill/filled.gds.gz', '84ffab59'),
    ('H0/netlist/fault_v_asic_top.nl.v', H0R + '/nl/fault_v_asic_top.nl.v', 'cdbbfc46'),
    ('H0/netlist/fault_v_asic_top.pnl.v', H0R + '/pnl/fault_v_asic_top.pnl.v', None),
    ('H0/constraints/constraints_reviewed.sdc', SDC, '979a8d3f'),
    ('H0/parasitics/fault_v_asic_top.min.spef', H0R + '/spef/min/fault_v_asic_top.min.spef', None),
    ('H0/parasitics/fault_v_asic_top.nom.spef', H0R + '/spef/nom/fault_v_asic_top.nom.spef', None),
    ('H0/parasitics/fault_v_asic_top.max.spef', H0R + '/spef/max/fault_v_asic_top.max.spef', None),
    ('H0/def/fault_v_asic_top.def', H0R + '/def/fault_v_asic_top.def', None),
    ('H0/reports/W25_Closure_Report.md', 'week25_closure/W25_Closure_Report.md', None),
    ('H0/reports/W25_closure_result.json', 'week25_closure/reports/W25_closure_result.json', None),
    ('H0/reports/final_post_verified.json', 'week25_closure/reports/final_post_verified.json', '07223c0c'),
    ('H0/reports/final_core_verified.json', 'week25_closure/reports/final_core_verified.json', 'd66a9bbd'),
    ('H0/reports/final_ir_verified.json', 'week25_closure/reports/final_ir_verified.json', '4cb99cf2'),
    ('H0/reports/final_fill_verified.json', 'week25_closure/reports/final_fill_verified.json', 'ebed20b9'),
    ('H0/reports/final_sliding_density.json', 'week25_closure/reports/final_sliding_density.json', None),
    ('H0/reports/final_em_resistor_audit.json', 'week25_closure/reports/final_em_resistor_audit.json', None),
    ('H0/reports/final_acceptance_criteria.json', 'week25_closure/controls/final_acceptance_criteria.json', None),
    ('H0/reports/flow_metrics.json', H0R + '/metrics.json', None),
    ('H0/reports/Reset_CDC_DFT_Review.md', 'week25_signoff/Reset_CDC_DFT_Review.md', '350f6942'),
    ('H0/reports/Pad_ESD_Package_Review.md', 'week25_signoff/Pad_ESD_Package_Review.md', 'e97fd35b'),
    ('H0/reports/Rule_Model_Coverage.md', 'week25_signoff/Rule_Model_Coverage.md', '3e9dd883'),
    # ---------------- H1 (h1c_pg_r1 -> h1c_post) ----------------
    ('H1/layout/fault_v_asic_top.gds', H1R + '/gds/fault_v_asic_top.gds', 'ae8a3f29'),
    ('H1/layout/fault_v_asic_top_filled.gds.gz', H1 + '/closure_c/final_fill/filled.gds.gz', '168b1621'),
    ('H1/netlist/fault_v_asic_top.nl.v', H1R + '/nl/fault_v_asic_top.nl.v', '5c11b7c5'),
    ('H1/netlist/fault_v_asic_top.pnl.v', H1R + '/pnl/fault_v_asic_top.pnl.v', None),
    ('H1/constraints/constraints_reviewed.sdc', SDC, '979a8d3f'),
    ('H1/parasitics/fault_v_asic_top.min.spef', H1R + '/spef/min/fault_v_asic_top.min.spef', None),
    ('H1/parasitics/fault_v_asic_top.nom.spef', H1R + '/spef/nom/fault_v_asic_top.nom.spef', 'bad7fcde'),
    ('H1/parasitics/fault_v_asic_top.max.spef', H1R + '/spef/max/fault_v_asic_top.max.spef', None),
    ('H1/def/fault_v_asic_top.def', H1R + '/def/fault_v_asic_top.def', None),
    ('H1/reports/H1_Definition.md', 'ppa/h1/H1_Definition.md', None),
    ('H1/reports/H1_PPA_result.json', 'ppa/formal_h1/reports/H1_PPA_result.json', None),
    ('H1/reports/H1_closure_result.json', H1 + '/closure_c/reports/H1_closure_result.json', None),
    ('H1/reports/h1_filled_independent_drc.json', H1 + '/closure_c/reports/h1_filled_independent.json', None),
    ('H1/reports/h1_filled_all_connectivity.json', H1 + '/closure_c/reports/h1_filled_all_connectivity.json', None),
    ('H1/reports/h1_macro_audit.json', H1 + '/closure_c/reports/h1_macro_audit.json', None),
    ('H1/reports/h1_stdcell_audit.json', H1 + '/closure_c/reports/h1_stdcell_audit.json', None),
    ('H1/reports/h1_pg_contacts.json', H1 + '/closure_c/reports/h1_pg_contacts.json', None),
    ('H1/reports/h1_em_resistor_audit.json', H1 + '/closure_c/reports/h1_em_resistor_audit.json', None),
    ('H1/reports/h1_ir_input.json', H1 + '/closure_c/reports/h1_ir_input.json', None),
    ('H1/reports/h1_sliding_density.json', H1 + '/closure_c/reports/h1_sliding_density.json', None),
    ('H1/reports/h1_sliding_density_H0die_misscoped.json', H1 + '/closure_c/reports/h1_sliding_density_H0die_misscoped.json', None),
    ('H1/reports/h1_dummy_grid.json', H1 + '/closure_c/reports/h1_dummy_grid.json', None),
    ('H1/reports/h1_fom_geometry.json', H1 + '/closure_c/reports/h1_fom_geometry.json', None),
    ('H1/reports/h1_fom_repair.json', H1 + '/closure_c/reports/h1_fom_repair.json', None),
    ('H1/reports/h1_li_repair.json', H1 + '/closure_c/reports/h1_li_repair.json', None),
    ('H1/reports/h1_fill_beol.rdb', H1 + '/closure_c/reports/h1_fill_beol.rdb', None),
    ('H1/reports/script_provenance.json', H1 + '/closure_c/reports/script_provenance.json', None),
    ('H1/reports/flow_metrics.json', H1R + '/metrics.json', None),
    # ---------------- shared: SRAM macro views used by both flows ----------------
    ('macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim_dedup.gds', 'week25_closure/macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim_dedup.gds', None),
    ('macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef', 'routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef', None),
    ('macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib', 'routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib', None),
    ('macros/sky130_sram_2kbyte_1rw1r_32x512_8_sim_model.v', 'design/macros/model.v', None),  # model used by every functional/activity simulation
    # ---------------- comparison + competition ----------------
    ('docs/H0_H1_PPA_Report.md', 'ppa/formal_h1/H0_H1_PPA_Report.md', None),
    ('docs/H0_H1_comparison.json', 'ppa/formal_h1/reports/H0_H1_comparison.json', None),
    ('docs/Fault-V_競賽報告書.pdf', 'w26/competition/Fault-V_競賽報告書.pdf', None),
    ('docs/Fault-V_競賽報告書.docx', 'w26/competition/Fault-V_競賽報告書.docx', None),
    ('reproduce/H0/Reproduce_W25.md', 'week25_closure/Reproduce_W25.md', None),
]
# whole script directories / script sets copied for reproduction (reference copies; they expect the /work repository layout)
SCRIPT_SETS = [
    ('reproduce/H0/week25_closure_scripts', 'week25_closure/scripts', '*'),
    ('reproduce/H1/closure_c_scripts', H1 + '/closure_c/scripts', '*.py'),
    ('reproduce/H1/closure_c', H1 + '/closure_c', 'run_*.sh'),
    ('reproduce/H1/closure_c', H1 + '/closure_c', 'setup_closure_c.py'),
    ('reproduce/H1/signoff', H1 + '/signoff', '*_c.*'),
    ('reproduce/H1/signoff', H1 + '/signoff', 'make_c.py'),
    ('reproduce/H1/signoff', H1 + '/signoff', 'plain_cli.py'),
    ('reproduce/H1/signoff', H1 + '/signoff', 'h1_lvs_cli.py'),
    ('reproduce/H1/signoff', H1 + '/signoff', 'sta_brief.py'),
    ('reproduce/H1/pg_repair', H1 + '/eco', 'pg_h1_fix*.py'),
    ('reproduce/H1/pg_repair', H1 + '/eco', 'h1c_driver.sh'),
    ('reproduce/H1/formal_ppa', 'ppa/formal_h1/scripts', '*h1c*'),
    ('reproduce/W26', 'w26/scripts', '*'),
]

def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()

def copy_verified(src, dst):
    assert src.is_file(), src
    assert not dst.exists(), f'refusing to overwrite {dst}'
    dst.parent.mkdir(parents=True, exist_ok=True)
    s = sha(src); part = dst.with_name(dst.name + '.part'); assert not part.exists()
    with open(src, 'rb') as a, open(part, 'wb') as b: shutil.copyfileobj(a, b, 8 << 20)
    assert sha(part) == s, f'copy mismatch {src}'
    part.rename(dst); return s

def cmd_copy():
    PKG.mkdir(parents=True, exist_ok=True)
    sources = {}
    for rel, src, exp in FILES:
        s = copy_verified(ROOT / src, PKG / rel)
        if exp: assert s.startswith(exp), f'{src}: sha {s[:8]} != expected {exp}'
        sources[rel] = {'source': src, 'sha256': s}
        print('COPIED', rel, s[:12], flush=True)
    for dst, src, pat in SCRIPT_SETS:
        for p in sorted((ROOT / src).glob(pat)):
            if p.is_file() and '.part' not in p.name and p.suffix != '.pyc':
                rel = f'{dst}/{p.name}'
                if (PKG / rel).exists(): continue
                sources[rel] = {'source': str(p.relative_to(ROOT)), 'sha256': copy_verified(p, PKG / rel)}
    (W26 / 'delivery' / 'sources.json').write_text(json.dumps(sources, indent=1, ensure_ascii=False) + '\n')
    print('COPY_DONE', len(sources), flush=True)

def cmd_finalize():
    for name in ('README.md', 'check_package.py'):
        src = W26 / 'delivery_src' / name; dst = PKG / name
        if dst.exists(): dst.unlink()
        shutil.copyfile(src, dst)
    files = sorted(p for p in PKG.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS', 'manifest.json'))
    assert not any(p.name.endswith('.part') for p in files)
    sources = json.loads((W26 / 'delivery' / 'sources.json').read_text())
    entries = []
    for p in files:
        rel = p.relative_to(PKG).as_posix(); s = sha(p)
        if rel in sources: assert sources[rel]['sha256'] == s, f'{rel} changed after copy'
        entries.append({'path': rel, 'bytes': p.stat().st_size, 'sha256': s, 'source': sources.get(rel, {}).get('source', 'generated in w26')})
    (PKG / 'SHA256SUMS').write_text(''.join(f"{e['sha256']}  {e['path']}\n" for e in entries))
    eq = {}
    for v in ('H0', 'H1'):
        for k in ('core', 'filled'):
            j = PKG / v / 'layout' / f'oasis_{k}_equivalence.json'
            d = json.loads(j.read_text())
            x = PKG / v / 'layout' / f'xor_{k}.json'
            xr = json.loads(x.read_text())
            eq[f'{v}_{k}'] = {'oasis_equivalent': d['equivalent'], 'negative_control_detected': d.get('negative_control', {}).get('detected'),
                              'flat_xor_items': xr['items'], 'flat_xor_layers': xr['layers']}
            assert d['equivalent'] and xr['items'] == 0 and xr['rc'] == 0, (v, k)
    manifest = {'package': 'Fault-V W26 delivery (H0 + H1)', 'created_unix': time.time(),
                'tool_image': 'ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302',
                'pdk': 'sky130A ciel 8afc8346a57fe1ab7934ba5a6056ea8b43078e71 (not included; standard cells and tech from this PDK)',
                'layout_equivalence': eq, 'file_count': len(entries), 'bytes': sum(e['bytes'] for e in entries), 'files': entries}
    (PKG / 'manifest.json').write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n')
    print('FINALIZE_DONE', len(entries), manifest['bytes'], json.dumps(eq), flush=True)

def cmd_zip():
    assert not ZIP.exists()
    part = ZIP.with_name(ZIP.name + '.part'); assert not part.exists()
    files = sorted(p for p in PKG.rglob('*') if p.is_file())
    with zipfile.ZipFile(part, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as z:
        for p in files: z.write(p, 'Fault-V_W26/' + p.relative_to(PKG).as_posix())
    sums = dict(reversed(l.split('  ', 1)) for l in (PKG / 'SHA256SUMS').read_text().splitlines())
    checked = 0
    with zipfile.ZipFile(part) as z:
        assert z.testzip() is None
        for info in z.infolist():
            rel = info.filename.split('/', 1)[1]
            if rel in ('SHA256SUMS', 'manifest.json'): continue
            h = hashlib.sha256()
            with z.open(info) as f:
                for chunk in iter(lambda: f.read(8 << 20), b''): h.update(chunk)
            assert h.hexdigest() == sums[rel], rel; checked += 1
    assert checked == len(sums), (checked, len(sums))
    part.rename(ZIP)
    (ZIP.with_name(ZIP.name + '.sha256')).write_text(f'{sha(ZIP)}  {ZIP.name}\n')
    print('ZIP_DONE', ZIP.stat().st_size, 'members_verified', checked, flush=True)

{'copy': cmd_copy, 'finalize': cmd_finalize, 'zip': cmd_zip}[sys.argv[1]]()
