"""H1 post-route inputs: H0's focus_post_b settings and step list, bound to the final H1 ECO round.

Usage (from cand_gap90x95, on the WSL host): python3 signoff/prepare_post_c.py <final ECO run tag, e.g. h1_eco_rf5>
Writes config_c_post.json (H0 config_focus_post_b.json with the H1 SRAM locations) and signoff/state_c_post.json.
Nothing under week25_closure / week25_signoff is written.
"""
import hashlib, json, sys
from pathlib import Path

cand = Path(__file__).resolve().parents[1]
root = cand.parents[2]
WD = '/work/ppa/h1/cand_gap90x95'
MACRO = 'sky130_sram_2kbyte_1rw1r_32x512_8'
tag = sys.argv[1]


def sha(p):
    with open(p, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


step = cand / 'runs' / tag / '01-openroad-detailedrouting'
res = json.loads((step / 'eco_result.json').read_text())
assert res['native_DRC'] == 0 and res['antenna_nets'] == 0, res
assert (step / 'fault_v_asic_top.drc').stat().st_size == 0
digest = sha(step / 'eco_final.odb')
assert digest == sha(step / 'fault_v_asic_top.odb')

state = json.loads((step / 'state_out.json').read_text())
assert state['odb'] == f'{WD}/runs/{tag}/01-openroad-detailedrouting/fault_v_asic_top.odb'
state.update(metrics={}, sdc='/work/week25_signoff/constraints_reviewed.sdc')
for key in ('gds', 'klayout_gds', 'spef', 'def'):
    state.pop(key, None)

cfg = json.loads((root / 'week25_closure/config_focus_post_b.json').read_text())
h1 = json.loads((cand / 'config_route.json').read_text())
assert cfg['meta']['flow'] == ['OpenROAD.FillInsertion', 'KLayout.StreamOut', 'KLayout.DRC',
                               'OpenROAD.CheckAntennas', 'OpenROAD.RCX']
assert cfg['SIGNOFF_SDC_FILE'] == '/work/week25_signoff/constraints_reviewed.sdc'
h0m, h1m = cfg['MACROS'][MACRO], h1['MACROS'][MACRO]
assert set(h0m['instances']) == set(h1m['instances']) and len(h1m['instances']) == 18
assert h0m['lef'] == h1m['lef'] and h0m['lib'] == h1m['lib'] and h0m['gds'] == h1m['gds']
h0m['instances'] = h1m['instances']

for path, value in ((cand / 'signoff/state_c_post.json', state), (cand / 'config_c_post.json', cfg)):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n')
(cand / 'signoff/reports_c').mkdir(exist_ok=True)
(cand / 'signoff/reports_c/post_input.json').write_text(json.dumps({
    'final_eco_run': tag, 'routed_odb_sha256': digest, 'native_DRC': 0, 'native_antenna_nets': 0,
    'config_source': 'week25_closure/config_focus_post_b.json with H1 SRAM locations',
    'sdc': '/work/week25_signoff/constraints_reviewed.sdc'}, indent=2) + '\n')
print('H1_POST_INPUT_READY', tag, digest)
