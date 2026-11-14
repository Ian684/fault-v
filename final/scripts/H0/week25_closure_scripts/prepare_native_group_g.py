from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/route_native_group_f.py').read_text().replace('native_group_f','native_group_g').replace('-or_seed 47 -or_k 7 -no_pin_access','-or_seed 53 -or_k 7')
assert '-no_pin_access' not in code
code=code.replace("'all_initial_routes_retained':True", "'all_initial_routes_retained':True,'native_pin_access_regenerated':True")
p=C/'scripts/route_native_group_g.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_G_REGENERATES_LEGAL_PIN_ACCESS_WITH_ROUTES_PROTECTED')
