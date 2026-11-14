from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/native_metal_planner_g.py').read_text()
code=code.replace('bounds=[1570000,627000,1597000,657000]', 'bounds=[1565000,620000,1605000,670000]')
code=code.replace("'data':{'vias':specs},'shapes':[]", "'data':{'vias':specs},'shapes':[],'existing':existing")
needle="    exec(compile(code,'existing_bounded_upper_metal_planner','exec'),env)"
assert code.count(needle)==1
replacement="    needle=\"    xs=sorted(x for x in xs if loX<=x<=hiX);ys=sorted(y for y in ys if loY<=y<=hiY)\"\n    code=code.replace(needle,\"    xs.update(x for x,y in existing if loX<=x<=hiX);ys.update(y for x,y in existing if loY<=y<=hiY)\\n\"+needle)\n"+needle
code=code.replace(needle,replacement)
code=code.replace(".replace('range((loX//50)*50,hiX+1,50)','range((loX//100)*100,hiX+1,100)').replace('range((loY//50)*50,hiY+1,50)','range((loY//100)*100,hiY+1,100)')", "")
code=code.replace("options=[(1583010,640730),(1582550,641410),(1582090,642090),(1581170,642770),(1580250,643450),(1579870,645490)]", "options=[(1579870,648890),(1579870,652290),(1579870,656370),(1583010,641410),(1582550,645490),(1580250,650930)]")
p=C/'scripts/native_metal_planner_i.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
code=(C/'scripts/repair_native_astar_g.py').read_text().replace('native_upper_g','native_upper_i').replace('from native_metal_planner_g import','from native_metal_planner_i import')
p=C/'scripts/repair_native_astar_i.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_EXACT_VIA_GRID_I_PREPARED')
