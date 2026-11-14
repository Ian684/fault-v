from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/native_metal_planner_g.py').read_text()
code=code.replace("b.findNet('net5547')", "b.findNet('net3347')")
code=code.replace("qa=('S','met2',1579410,639370,1584010,639370,70,70);qz=('S','met2',1584010,639370,1584010,657390,70,70)", "qa=('S','met2',1579870,638690,1584010,638690,70,70);qz=('S','met2',1584470,639370,1584470,642430,70,70)\n    middle=Counter([('S','met2',1584010,638690,1584010,639370,70,70),('S','met2',1584010,639370,1584470,639370,70,70)]);assert not middle-original")
code=code.replace("options=[(1583010,640730),(1582550,641410),(1582090,642090),(1581170,642770),(1580250,643450),(1579870,645490)]", "options=[(1583010,641070),(1582550,641750),(1582090,642100),(1581170,642300),(1580250,642360)]")
code=code.replace("start=(px,639370,2);end=(1584010,ry,2);roi=[px-8000,639370-8000,1584010+8000,ry+8000]", "start=(px,638690,2);end=(1584470,ry,2);roi=[px-8000,638690-8000,1584470+8000,ry+8000]")
code=code.replace("original-Counter([qa,qz])+Counter([piece('met2',(1579410,639370),start[:2]),piece('met2',end[:2],(1584010,657390))])", "original-Counter([qa,qz])-middle+Counter([piece('met2',(1579870,638690),start[:2]),piece('met2',end[:2],(1584470,642430))])")
p=C/'scripts/native_metal_planner_h.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
code=(C/'scripts/repair_native_astar_g.py').read_text().replace('native_upper_g','native_upper_h').replace('from native_metal_planner_g import','from native_metal_planner_h import')
p=C/'scripts/repair_native_astar_h.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_OTHER_CORNER_H_PREPARED')
