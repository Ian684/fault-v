from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs_g.py').read_text().replace('antenna_stubs_g','antenna_stubs_i').replace('reports/antenna_stubs_f/result.json','reports/antenna_stubs_h/incomplete.json').replace("if row['net'] in ('_10658_','net6033'):continue","if row['net']=='net6033':continue")
marker='original_wires=wires(b)'
assert code.count(marker)==1
code=code.replace(marker,"from relocate_antenna_diode import relocate\nrelocation=relocate(design,db,b,targets,C,'antenna_stubs_i')\nbefore=fixed(b)\n"+marker)
marker="    current=check(row['diode']+'_before',roi);found=False;goals=[]"
assert code.count(marker)==1;code=code.replace(marker,marker+"\n    assert not current,('Relocation baseline must be independently clean',current)")
p=C/'scripts/append_antenna_stubs_i.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('RELOCATED_PASSIVE_STUB_I_PREPARED')
