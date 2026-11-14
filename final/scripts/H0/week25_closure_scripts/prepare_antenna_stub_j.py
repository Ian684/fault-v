from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs_i.py').read_text().replace('antenna_stubs_i','antenna_stubs_j')
p=C/'scripts/append_antenna_stubs_j.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('RELOCATED_PASSIVE_STUB_J_PREPARED')
