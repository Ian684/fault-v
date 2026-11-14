"""Read-only: key 3-RC STA metrics of a run. Usage: python3 signoff/sta_brief.py runs/<tag>"""
import json, sys
from pathlib import Path
run = Path(sys.argv[1])
hits = sorted(run.glob('*/state_out.json'))
m = json.loads(hits[-1].read_text())['metrics']
print(hits[-1], len(m), 'metrics')
keys = ('timing__setup__ws', 'timing__hold__ws', 'timing__setup__tns', 'timing__hold__tns', 'timing__setup_vio__count',
        'timing__hold_vio__count', 'design__max_slew_violation__count', 'design__max_cap_violation__count',
        'design__max_fanout_violation__count', 'timing__unannotated_net__count', 'timing__unannotated_net_filtered__count')
for k in keys:
    row = {c.split(':', 1)[1] if ':' in c else 'all': v for c, v in m.items() if c == k or c.startswith(k + '__corner:')}
    print(f'{k:45s}', '  '.join(f'{c}={v}' for c, v in sorted(row.items())))
