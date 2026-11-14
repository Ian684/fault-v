from pathlib import Path
import json,re
from reviewed_drivers import load_driver_review
C=Path(__file__).resolve().parents[1]
state=json.loads((C/'runs/focus_post_a/5-openroad-rcx/state_out.json').read_text())
netlist=C/'runs/focus_post_a/1-openroad-fillinsertion/fault_v_asic_top.nl.v'
text=netlist.read_text()
drivers,_=load_driver_review(C)
for name,record in drivers.items():
    assert re.search(re.escape(record['master'])+r'\s+'+re.escape(name)+r'\s*\(',text),name
cfg=json.loads((C.parent/'week25_signoff/config_sta.json').read_text())
sta={'nl':'/work/week25_closure/runs/focus_post_a/1-openroad-fillinsertion/fault_v_asic_top.nl.v','spef':{f'{rc}_tt_025C_1v80':state['spef'][f'{rc}_*'] for rc in ('nom','min','max')},'metrics':{}}
(C/'focus_post_sta_state.json').write_text(json.dumps(sta,indent=2)+'\n')
(C/'config_focus_post_sta.json').write_text(json.dumps(cfg,indent=2)+'\n')
print(len(drivers),'reviewed drivers verified in fresh exported NL; three fresh RC SPEFs bound.',flush=True)
