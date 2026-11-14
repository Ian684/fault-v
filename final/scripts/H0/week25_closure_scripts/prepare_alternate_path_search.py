from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'controls/final_paths_a_impl.py').read_text()
code=code.replace('reports/final_paths_a','reports/final_paths_b').replace('final_paths_a.odb','final_paths_b.odb')
start=code.index('plans=[\n');end=code.index('\naccepted=[];',start)
code=code[:start]+'''plans=[
 ('net6342',[segment('met2',(1608850,633250),(1612070,633250)),segment('met2',(1612070,633250),(1612070,636140))],(1608850,633250,2),(1612070,636140,2)),
 ('_03544_',[segment('met2',(1613910,629340),(1613910,630870)),segment('met2',(1613910,630870),(1614370,630870)),segment('met2',(1614370,630870),(1614370,631210)),segment('met2',(1614370,631210),(1614395,631210)),segment('met2',(1614395,631210),(1614395,631550)),segment('met2',(1614395,631550),(1616210,631550))],(1613910,629340,2),(1616210,631550,2)),
 ('_09360_',[segment('met1',(1588105,636650),(1595970,636650))],(1588105,636650,1),(1595970,636650,1)),
]'''+code[end:]
code=code.replace("min(start[0],end[0])-4000,min(start[1],end[1])-4000,max(start[0],end[0])+4000,max(start[1],end[1])+4000", "min(start[0],end[0])-6000,min(start[1],end[1])-6000,max(start[0],end[0])+6000,max(start[1],end[1])+6000")
# Enlarge inventory and verification together; changed geometry must remain inside this box.
code=code.replace('region=[1575000,622000,1622000,649000]', 'region=[1575000,620000,1628000,650000]')
code=code.replace('1578000 625000 1620000 646000','1575000 620000 1628000 650000')
p=C/'controls/final_paths_b_impl.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,encoding='utf-8')
