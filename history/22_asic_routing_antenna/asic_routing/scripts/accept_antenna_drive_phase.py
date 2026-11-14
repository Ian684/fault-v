from pathlib import Path
import json,sys
r=Path(__file__).resolve().parents[1]
diodes=json.loads((r/'reports'/sys.argv[1]/'antenna_diode_checks.json').read_text());assert diodes['equivalent_driver_repair_verified']
p=Path(__file__).with_name('accept_antenna_both8_phase.py');code=p.read_text()
for old,new in [('scripts/antenna_both8_cli.py','scripts/antenna_drive_cli.py'),('antenna_both8_state.json','antenna_drive_state.json')]:
    assert code.count(old)==1
    code=code.replace(old,new)
exec(compile(code,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
