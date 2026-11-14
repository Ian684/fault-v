"""Select the next driver sizes using analysis-only unchanged-wire STA feedback."""
from pathlib import Path
import ast,hashlib,json,re
C=Path(__file__).resolve().parents[1];R=C.parent/'routing'
lib=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib'
text=lib.read_text();tree=ast.parse((R/'scripts/prepare_antenna_drive.py').read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='logic')
exec(compile(ast.Module(body=[function],type_ignores=[]),'logic','exec'))
assert logic('sky130_fd_sc_hd__buf_1')!=logic('sky130_fd_sc_hd__nor2_2')
viol=json.loads((C/'reports/probe50_electrical_violations.json').read_text())
drivers={r['driver'].rsplit('/',1)[0]:r['driver_master'] for rows in viol['violations'].values() for r in rows}
existing=json.loads((C/'reports/cached_input.json').read_text())['equivalent_drivers']
assert len(drivers)==17 and not(set(drivers)&set(existing))
source=C/'runs/probe50_rc_a/1-openroad-fillinsertion/fault_v_asic_top.nl.v';nl=source.read_text();changes={}
for name,old in sorted(drivers.items()):
    stem,number=old.rsplit('_',1);new=stem+'_'+str(2*int(number));assert logic(old)==logic(new)
    pattern=re.escape(old)+r'(\s+'+re.escape(name)+r'\s*\()'
    nl,count=re.subn(pattern,lambda m:new+m[1],nl);assert count==1,(name,count)
    changes[name]={'old':old,'new':new,'same_function_and_pin_contract':True}
target=C/'inputs/projected67.nl.v';assert not target.exists();target.write_text(nl)
state=json.loads((C/'probe50_sta_state.json').read_text());state['nl']='/work/week25_closure/inputs/projected67.nl.v';state['metrics']={}
(C/'projected67_sta_state.json').write_text(json.dumps(state,indent=2)+'\n')
proof={'accepted':False,'additional_drivers':changes,'total_drivers_relative_to_F':67,'source_netlist_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'projected_netlist_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'same_boolean_pin_contracts':True,'scope':'Analysis-only size selection using old physical wire parasitics. No placement/routing changed or accepted. This cannot substitute for fresh extraction after physical ECO; all final checks remain required.'}
(C/'reports/projected67_input.json').write_text(json.dumps(proof,indent=2)+'\n')
print('PROJECTED67_STA_READY',len(changes),'additional equivalent drivers; analysis only')
