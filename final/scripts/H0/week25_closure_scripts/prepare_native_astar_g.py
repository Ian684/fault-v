from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/native_metal_planner.py').read_text()
code=code.replace("('met2','met3','met4')", "('met1','met2','met3','met4')")
code=code.replace("('met2','met3','met4','met5')", "('met1','met2','met3','met4','met5')")
code=code.replace("spacing={'met2':140", "spacing={'met1':140,'via':170,'met2':140")
code=code.replace("options=[(1583010,640730)", "options=[(1583010,640730)")
p=C/'scripts/native_metal_planner_g.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
code=(C/'scripts/repair_native_astar.py').read_text().replace('native_upper_f','native_upper_g').replace('from native_metal_planner import','from native_metal_planner_g import')
p=C/'scripts/repair_native_astar_g.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_M1_M5_PLANNER_G_PREPARED')
