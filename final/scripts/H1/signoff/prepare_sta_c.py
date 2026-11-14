"""H1 3-RC STA inputs (H0 focus_post_sta_b method): filled netlist + fresh nom/min/max SPEF from runs/h1c_post.

Usage (from cand_gap90x95, WSL host): python3 signoff/prepare_sta_c.py
Writes config_c_sta3.json (week25_signoff/config_sta.json unchanged apart from H1 SRAM locations, if it lists any)
and signoff/state_c_sta.json.
"""
import json, re
from pathlib import Path

cand = Path(__file__).resolve().parents[1]
root = cand.parents[2]
WD = '/work/ppa/h1/cand_gap90x95'
MACRO = 'sky130_sram_2kbyte_1rw1r_32x512_8'


def one(pattern):
    hits = sorted((cand / 'runs/h1c_post').glob(pattern))
    assert len(hits) == 1, (pattern, hits)
    return hits[0]


assert (cand / 'signoff/logs_c/h1c_post.exit').read_text().strip() == '0'
fill = one('*-openroad-fillinsertion')
rcx = json.loads((one('*-openroad-rcx') / 'state_out.json').read_text())
nl = f'{WD}/runs/h1c_post/{fill.name}/fault_v_asic_top.nl.v'
assert rcx['nl'] == nl, rcx['nl']
text = (fill / 'fault_v_asic_top.nl.v').read_text()
# Instances named by the reviewed SDC and timing_extra.tcl must exist in the H1 netlist.
for name in '_54687_ _54688_ _54689_ _52931_ _52933_ _52932_ _52934_ _53019_ _53020_'.split():
    assert re.search(r'sky130_fd_sc_hd__df\w+\s+' + name + r'\s*\(', text), name
spef = {f'{rc}_tt_025C_1v80': rcx['spef'][f'{rc}_*'] for rc in ('nom', 'min', 'max')}
for path in spef.values():
    assert (cand / Path(path).relative_to(WD)).stat().st_size > 1000000, path

cfg = json.loads((root / 'week25_signoff/config_sta.json').read_text())
assert cfg['STA_CORNERS'] == ['nom_tt_025C_1v80', 'min_tt_025C_1v80', 'max_tt_025C_1v80']
assert cfg['SIGNOFF_SDC_FILE'] == '/work/week25_signoff/constraints_reviewed.sdc'
if 'instances' in cfg.get('MACROS', {}).get(MACRO, {}):
    h1 = json.loads((cand / 'config_route.json').read_text())
    cfg['MACROS'][MACRO]['instances'] = h1['MACROS'][MACRO]['instances']
state = {'nl': nl, 'spef': spef, 'metrics': {}}
for path, value in ((cand / 'signoff/state_c_sta.json', state), (cand / 'config_c_sta3.json', cfg)):
    assert not path.exists(), path
    path.write_text(json.dumps(value, indent=2) + '\n')
print('H1_STA_INPUT_READY', nl)
