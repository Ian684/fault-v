from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_native_group_k.py').read_text().replace('native_group_k','native_group_l')
assert code.count('failed=[]\n')==1
code=code.replace('failed=[]\n','failed=[];resumed=set()\n')
p=C/'scripts/append_native_group_l.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_L_M1_ACCESS_TRIAL_PREPARED')
