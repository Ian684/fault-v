from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/repair_native_upper.py').read_text().replace('native_upper_b','native_upper_f')
marker="done=False\nfor name in re.findall(r'net:([^\\s]+)',marker['srcs']):";assert code.count(marker)==1
new="from native_metal_planner import repair_corner\nrecord=repair_corner(design,db,b,out,normalize_routes,connectivity)\ndone=record is not None\nif done:repairs.append(record)\nfor name in ([] if done else re.findall(r'net:([^\\s]+)',marker['srcs'])):"
code=code.replace(marker,new)
p=C/'scripts/repair_native_astar.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_UPPER_OBSTACLE_REPAIR_PREPARED')
