from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs_e.py').read_text().replace('antenna_stubs_e','antenna_stubs_f').replace('reports/antenna_stubs_d/incomplete.json','reports/antenna_stubs_e/incomplete.json').replace('reports/antenna_stub_targets.json','reports/antenna_stub_full_targets.json')
marker="            found=True;print('DIODE_STUB_ACCEPTED',row['diode'],name,len(path),flush=True);break"
assert code.count(marker)==1
code=code.replace(marker,"            (out/'progress.json').write_text(json.dumps({'accepted':accepted,'accepted_for_final':False},indent=2)+'\\n')\n"+marker)
p=C/'scripts/append_antenna_stubs_f.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('FULL_NATIVE_TARGET_STUB_F_PREPARED')
