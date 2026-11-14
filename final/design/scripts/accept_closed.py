from pathlib import Path
import sys,json,hashlib,shutil
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]
run=R/'runs'/tag
m=json.loads((run/'final/metrics.json').read_text())
for key in ['design__max_slew_violation__count','design__max_cap_violation__count','timing__setup_vio__count','timing__hold_vio__count']:
 assert m[key]==0,(key,m[key])
assert m['timing__setup__ws']>0 and m['timing__hold__ws']>0
net=run/'final/nl/fault_v_asic_top.nl.v'
assert net.read_bytes()==(R/'eco/fault_v_asic_top.nl.v').read_bytes()
proof=json.loads((R/'eco/connectivity_proof.json').read_text())
assert proof['pass'] and proof['netlist_sha256']==hashlib.sha256(net.read_bytes()).hexdigest()
shutil.copy2(net,R/'mapped_top.v')
(R/'eco/accepted_run.json').write_text(json.dumps({'run':tag,'metrics':m,'netlist_sha256':proof['netlist_sha256']},indent=2)+'\n')
print('PASS serialized final netlist, connectivity and TT setup/hold/slew/cap checks.')
