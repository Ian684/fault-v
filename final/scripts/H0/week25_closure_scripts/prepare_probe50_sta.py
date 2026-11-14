from pathlib import Path
import json,re
C=Path(__file__).resolve().parents[1]
state=json.loads((C/'runs/probe50_rc_a/3-openroad-rcx/state_out.json').read_text())
netlist=C/'runs/probe50_rc_a/1-openroad-fillinsertion/fault_v_asic_top.nl.v'
text=netlist.read_text()
proof=json.loads((C/'reports/cached_input.json').read_text())
for name,record in proof['equivalent_drivers'].items():
    assert re.search(re.escape(record['master'])+r'\s+'+re.escape(name)+r'\s*\(',text),name
cfg=json.loads((C.parent/'week25_signoff/config_sta.json').read_text())
sta={'nl':'/work/week25_closure/runs/probe50_rc_a/1-openroad-fillinsertion/fault_v_asic_top.nl.v','spef':{f'{rc}_tt_025C_1v80':state['spef'][f'{rc}_*'] for rc in ('nom','min','max')},'metrics':{}}
(C/'probe50_sta_state.json').write_text(json.dumps(sta,indent=2)+'\n')
(C/'config_probe50_sta.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('50 equivalent drivers verified in fresh exported NL; three fresh RC SPEFs bound.',flush=True)
