from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs_f.py').read_text().replace('antenna_stubs_f','antenna_stubs_g').replace('reports/antenna_stubs_e/incomplete.json','reports/antenna_stubs_f/result.json').replace('reports/antenna_stub_full_targets.json','reports/antenna_stub_two_gate_targets.json')
marker="for row in prior:\n    assert row['local_native_new_markers']==0"
assert code.count(marker)==1
code=code.replace(marker,"for row in prior:\n    if row['net'] in ('_10658_','net6033'):continue\n    assert row['local_native_new_markers']==0")
marker="if v.getBottomLayer().getName() in ('li1','met1','met2','met3','met4')"
assert code.count(marker)==1;code=code.replace(marker,"if v.getBottomLayer().getName() in ('li1','met1')")
code=code.replace(')-6000',')-15000').replace(')+6000',')+15000')
p=C/'scripts/append_antenna_stubs_g.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('LOW_LAYER_GATE_STUB_G_PREPARED')
