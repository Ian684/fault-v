"""Generate the "c"-pass copies of the verified b-pass signoff scripts (only names of tags, files and folders change).

The b pass (h1b_*) stays untouched as the pre-PG-repair record. The c pass signs off the PG-repaired candidate:
  runs/h1c_post, h1c_sta, h1c_lvs, h1c_lvs_bad, functional/h1c_a, signoff/logs_c, signoff/reports_c,
  config_c_post.json / config_c_sta3.json / config_c_lvs.json, signoff/state_c_*.json,
  signoff/h1c_core_lvs.gds / h1c_badpin_lvs.gds, ppa/formal_h1/logs/power_h1c.*
Usage (from cand_gap90x95, WSL host): python3 signoff/make_c.py     (refuses to overwrite)
"""
import re
from pathlib import Path

cand = Path(__file__).resolve().parents[1]
formal = cand.parents[1] / 'formal_h1'
SCRIPTS = 'prepare_post|prepare_sta|prepare_lvs|run_flow|run_functional|run_signoff|run_activity_cov|export_activity_targets|analyze_activity_h1'
RULES = [
    (r'\bh1b_(post|sta|lvs_bad|lvs|a)\b', r'h1c_\1'),
    (r'\bh1b_(core_lvs|badpin_lvs)', r'h1c_\1'),
    (r'\bconfig_b_(post|sta3|lvs)\.json', r'config_c_\1.json'),
    (r'\bstate_b_(post|sta|lvs_bad|lvs)\.json', r'state_c_\1.json'),
    (r'signoff/(logs|reports)_b\b', r'signoff/\1_c'),
    (r'signoff/(' + SCRIPTS + r')_b\.(py|sh)', r'signoff/\1_c.\2'),
    (r'faultv-h1b-', 'faultv-h1c-'),
    (r'faultv-ppa-h1b-power', 'faultv-ppa-h1c-power'),
    (r'\b(run_)?power_h1b\b', r'\1power_h1c'),
]
jobs = [(cand / 'signoff' / f'{n}_b.{e}', cand / 'signoff' / f'{n}_c.{e}') for n, e in (
    ('prepare_post', 'py'), ('prepare_sta', 'py'), ('prepare_lvs', 'py'), ('run_flow', 'sh'), ('run_functional', 'py'),
    ('run_signoff', 'sh'), ('run_activity_cov', 'sh'), ('export_activity_targets', 'py'), ('analyze_activity_h1', 'py'))]
jobs += [(formal / 'scripts/run_power_h1b.sh', formal / 'scripts/run_power_h1c.sh'),
         (formal / 'scripts/power_h1b.tcl', formal / 'scripts/power_h1c.tcl')]
for src, dst in jobs:
    assert not dst.exists(), dst
for src, dst in jobs:
    text = src.read_text(encoding='utf-8')
    n = 0
    for pat, rep in RULES:
        text, k = re.subn(pat, rep, text)
        n += k
    leftover = sorted(set(re.findall(r'h1b_\w+|_b\.(?:py|sh)|logs_b|reports_b|state_b_\w+|config_b_\w+', text)))
    dst.write_text(text, encoding='utf-8', newline='\n')
    print(f'{dst.relative_to(cand.parents[1])}: {n} replacements; remaining b-names: {leftover}')
