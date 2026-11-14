from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_native_group_t.py').read_text().replace('native_group_t','native_group_u')
old="old=expected[row['diode']];assert list(old[1])==row['old_location'];expected[row['diode']]=(old[0],tuple(row['new_location']),*old[2:])"
new="old=expected[row['diode']];assert list(old[2])==row['old_location'];expected[row['diode']]=(old[0],old[1],tuple(row['new_location']),old[3])"
assert code.count(old)==1;code=code.replace(old,new)
p=C/'scripts/append_native_group_u.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,newline='\n')
sh=(C/'scripts/run_native_group_t.sh').read_text().replace('native_group_t','native_group_u').replace('native-group-t','native-group-u').replace('antenna_native_t','antenna_native_u')
(C/'scripts/run_native_group_u.sh').write_text(sh,newline='\n')
print('U_FIXED_LOCATION_TUPLE_AND_PRESERVES_ORIENTATION_STATUS')
