"""H1 core/pin-interface LVS inputs (H0 final_core_lvs method) for the good view and the shifted-pin negative control.

Usage (from cand_gap90x95, WSL host), after build_core_lvs_view.py wrote signoff/h1c_core_lvs.gds and
signoff/h1c_badpin_lvs.gds: python3 signoff/prepare_lvs_c.py
Writes config_c_lvs.json, signoff/state_c_lvs.json and signoff/state_c_lvs_bad.json.
"""
import hashlib, json
from pathlib import Path

cand = Path(__file__).resolve().parents[1]
WD = '/work/ppa/h1/cand_gap90x95'


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def one(pattern):
    hits = sorted((cand / 'runs/h1c_post').glob(pattern))
    assert len(hits) == 1, (pattern, hits)
    return hits[0]


assert (cand / 'signoff/logs_c/h1c_post.exit').read_text().strip() == '0'
state = json.loads((one('*-klayout-drc') / 'state_out.json').read_text())
gds = one('*-klayout-streamout') / 'fault_v_asic_top.gds'
view = json.loads((cand / 'signoff/reports_c/h1c_core_lvs_view.json').read_text())
assert sha(gds) == view['manufacturing_source_GDS_sha256']
assert len(view['pin_names']) == 125 and view['SRAM_instances'] == 18
assert sha(cand / 'signoff/h1c_core_lvs.gds') == view['LVS_only_view_sha256']
assert sha(cand / 'signoff/h1c_badpin_lvs.gds') == view['intentional_bad_pin_view_sha256']

cfg = json.loads((cand / 'config_c_post.json').read_text())
assert cfg['MAGIC_EXT_ABSTRACT_CELLS'] == ['^sky130_sram_2kbyte_1rw1r_32x512_8$'] and cfg['MAGIC_EXT_USE_GDS']
cfg['meta'] = {'version': 2, 'flow': ['Magic.SpiceExtraction', 'Netgen.LVS']}
state.pop('spef', None)
state['metrics'] = {}
outputs = [(cand / 'config_c_lvs.json', cfg)]
for name, view_gds in (('state_c_lvs.json', 'h1c_core_lvs.gds'), ('state_c_lvs_bad.json', 'h1c_badpin_lvs.gds')):
    s = dict(state, gds=f'{WD}/signoff/{view_gds}', klayout_gds=f'{WD}/signoff/{view_gds}')
    outputs.append((cand / 'signoff' / name, s))
for path, value in outputs:
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n')
print('H1_LVS_INPUT_READY', view['LVS_only_view_sha256'])
