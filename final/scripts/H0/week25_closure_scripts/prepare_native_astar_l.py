from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/native_metal_planner_i.py').read_text()
code=code.replace("b.findNet('net5547')", "b.findNet('net3347')")
code=code.replace("qa=('S','met2',1579410,639370,1584010,639370,70,70);qz=('S','met2',1584010,639370,1584010,657390,70,70)", "qa=('S','met2',1580330,639370,1583550,639370,70,70);qz=('S','met2',1583550,639370,1583550,643450,70,70)")
code=code.replace("options=[(1579870,648890),(1579870,652290),(1579870,656370),(1583010,641410),(1582550,645490),(1580250,650930)]", "options=[(1582090,641070),(1581630,642430),(1581170,643300),(1582550,640390),(1580630,643380)]")
code=code.replace("start=(px,639370,2);end=(1584010,ry,2);roi=[px-8000,639370-8000,1584010+8000,ry+8000]", "start=(px,639370,2);end=(1583550,ry,2);roi=[px-8000,639370-8000,1583550+8000,ry+8000]")
code=code.replace("piece('met2',(1579410,639370),start[:2]),piece('met2',end[:2],(1584010,657390))", "piece('met2',(1580330,639370),start[:2]),piece('met2',end[:2],(1583550,643450))")
p=C/'scripts/native_metal_planner_l.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
code=(C/'scripts/repair_native_astar.py').read_text().replace('native_upper_f','native_upper_l').replace('from native_metal_planner import','from native_metal_planner_l import')
code=code.replace("source=Path('/runtime/antenna_native12.odb')", "source=Path('/runtime_final/native_group_c.odb')")
code=code.replace("['source_sha256']", "['output_sha256']",1).replace('reports/antenna_iter12_probe.json','reports/native_group_c/result.json',1).replace('reports/antenna_iter12_independent.json','reports/native_group_c_independent.json',1)
p=C/'scripts/repair_native_astar_l.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_C_CORNER_L_PREPARED')
