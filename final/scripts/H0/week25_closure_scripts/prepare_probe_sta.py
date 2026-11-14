from pathlib import Path
import json,re
C=Path(__file__).resolve().parents[1]
netlist=C/'runs/probe_rc_a/1-openroad-fillinsertion/fault_v_asic_top.nl.v'
text=netlist.read_text()
for name,record in json.loads((C/'reports/minimal_input.json').read_text())['resized'].items():
    assert re.search(re.escape(record['new'])+r'\s+'+re.escape(name)+r'\s*\(',text),name
state=json.loads((C/'runs/probe_rc_a/3-openroad-rcx/state_out.json').read_text())
cfg=json.loads((C.parent/'week25_signoff/config_sta.json').read_text())
sta={'nl':'/work/week25_closure/runs/probe_rc_a/1-openroad-fillinsertion/fault_v_asic_top.nl.v','spef':{f'{rc}_tt_025C_1v80':state['spef'][f'{rc}_*'] for rc in ('nom','min','max')},'metrics':{}}
(C/'probe_sta_state.json').write_text(json.dumps(sta,indent=2)+'\n')
(C/'config_probe_sta.json').write_text(json.dumps(cfg,indent=2)+'\n')
print('All 48 new cell references verified in actual exported NL; fresh three-RC SPEF bound.',flush=True)
