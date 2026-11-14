from pathlib import Path
import hashlib,json,sys
r=Path(__file__).resolve().parents[1];tag=sys.argv[1];a=json.loads((r/'reports'/f'{tag}_launch.json').read_text())
proof=json.loads((r/'reports'/f"{a['global_run']}_input.json").read_text());assert proof['final_global_verified'] and proof['total_overflow']==0
assert proof['source_sha256']==hashlib.sha256((r/'runs'/tag/'final/odb/fault_v_asic_top.odb').read_bytes()).hexdigest()
diodes=json.loads((r/'reports'/tag/'antenna_diode_checks.json').read_text());assert diodes['equivalent_driver_repair_verified']
p=Path(__file__).with_name('accept_antenna_both8_phase.py');code=p.read_text()
for old,new in [('scripts/antenna_both8_cli.py','scripts/antenna_drive_finish_cli.py'),('antenna_both8_state.json','antenna_drive_finish_state.json')]:
    assert code.count(old)==1
    code=code.replace(old,new)
exec(compile(code,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
