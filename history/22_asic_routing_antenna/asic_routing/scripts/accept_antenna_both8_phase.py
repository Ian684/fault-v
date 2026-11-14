from pathlib import Path
import hashlib,json,sys
p=Path(__file__).with_name('accept_antenna_phase.py');r=p.parents[1];code=p.read_text()
launch=json.loads((r/'reports'/f'{sys.argv[1]}_launch.json').read_text());g=launch['global_run']
checks=r/'reports'/g/'global_checks.json';proof=json.loads(checks.read_text())
assert proof['pass'] and proof['total_overflow']==0
assert hashlib.sha256(checks.read_bytes()).hexdigest()==launch['sha256'][checks.relative_to(r).as_posix()]
needle="    'scripts/antenna_resume_cli.py':'antenna_resume_state.json',"
assert code.count(needle)==1
code=code.replace(needle,needle+"\n    'scripts/antenna_both8_cli.py':'antenna_both8_state.json',")
code=code.replace("'global_desktop_joint_corner'",repr(g))
code=code.replace('Zero-overflow global parent before antenna repair; final repair geometry separately passes native and independent routing DRC.','Zero-overflow native global guides generated after all diode placement and corner constraints; final detailed geometry separately passes native and independent routing DRC.')
exec(compile(code,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
