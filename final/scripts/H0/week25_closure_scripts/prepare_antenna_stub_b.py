"""Resume checked stubs and prevent new cuts colliding with existing same-net cuts."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs.py').read_text().replace('antenna_stubs_a','antenna_stubs_b')
marker="exec(compile(source.replace('time.monotonic()-began>180','time.monotonic()-began>35'),'bounded_existing_local_planner','exec'))"
assert code.count(marker)==1
code=code.replace(marker,"assert source.count('if n==net:continue')==1\nsource=source.replace('if n==net:continue','if n==net and l in width:continue')\n"+marker)
marker='accepted=[];paths=defaultdict(list)'
assert code.count(marker)==1
code=code.replace(marker,marker+'''
prior=json.loads((C/'reports/antenna_stubs_a/incomplete.json').read_text())['accepted']
resumed=set()
for row in prior:
    assert row['local_native_new_markers']==0 and row['diode'] in access['borrowed_native_accesses']
    assert access['borrowed_native_accesses'][row['diode']]['signal_net']==row['net']
    added=append(b.findNet(row['net']),row['path'])
    assert added==Counter(map(tuple,row['added_primitives']))
    accepted.append({**row,'checked_in_previous_trial':'antenna_stubs_a'})
    paths[row['net']].append(row['path']);resumed.add(row['diode'])
    for q in added.elements():add_primitive(q,row['net'])
print('RESUMED_CHECKED_STUBS',len(resumed),flush=True)
''')
marker='for row,roi in zip(targets,regions):'
assert code.count(marker)==1;code=code.replace(marker,marker+"\n    if row['diode'] in resumed:continue")
p=C/'scripts/append_antenna_stubs_b.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('CUT_AWARE_STUB_B_PREPARED')
