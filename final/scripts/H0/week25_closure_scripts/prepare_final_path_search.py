"""Derive a fresh, bounded three-dimensional search from the audited path editor."""
from pathlib import Path

C = Path(__file__).resolve().parents[1]
code = (C / 'scripts/search_short_paths.py').read_text()
code = code.replace("source=Path('/runtime/focus_final.odb')", "source=Path('/route_b/1-openroad-detailedrouting/native_final.odb')")
code = code.replace("out=C/('reports/short_paths_fine' if fine else 'reports/short_paths_b')", "out=C/'reports/final_paths_a'")
code = code.replace('region=[1575000,625000,1618000,649000]', 'region=[1575000,622000,1622000,649000]')
code = code.replace("('met1','met2','met3')", "('met1','met2','met3','met4')")
start = code.index("spacing={'met1'")
end = code.index('\ndef check(tag):', start)
planner = (C / 'scripts/compressed_path_planner.py').read_text()
code = code[:start] + planner + code[end:]
code = code.replace('1579000 630000 1615000 646000', '1578000 625000 1620000 646000')
code = code.replace("assert sum(current.values())==7", "assert sum(current.values())==4")
start = code.index('plans=[\n')
end = code.index('\naccepted=[];', start)
code = code[:start] + '''plans=[
 ('net4985',[segment('met2',(1591830,631380),(1591830,636310)),('T','M1M2_PR',1591830,636310),segment('met1',(1591830,636310),(1591830,637670))],(1591830,631380,2),(1591830,637670,1)),
 ('_03545_',[segment('met2',(1613910,631550),(1614325,631550)),segment('met2',(1614325,631550),(1614325,632060)),segment('met2',(1614325,632060),(1614370,632060))],(1613910,631550,2),(1614370,632060,2)),
 ('net4469',[segment('met2',(1610690,632910),(1611780,632910)),segment('met2',(1611780,632910),(1611780,634270)),segment('met2',(1611610,634270),(1611780,634270))],(1610690,632910,2),(1611610,634270,2)),
]''' + code[end:]
code = code.replace('min(start[0],end[0])-5060,min(start[1],end[1])-5100,max(start[0],end[0])+5060,max(start[1],end[1])+5100', 'min(start[0],end[0])-4000,min(start[1],end[1])-4000,max(start[0],end[0])+4000,max(start[1],end[1])+4000')
code = code.replace("name='short_paths_fine.odb' if fine else 'short_paths.odb'", "name='final_paths_a.odb'")
code = code.replace("assert not missing and not disconnected,('Disconnected proposed path',name)", "assert not missing and not disconnected,('Disconnected proposed path',name)")
target = C / 'controls/final_paths_a_impl.py'
assert not target.exists()
compile(code, str(target), 'exec')
target.write_text(code, encoding='utf-8')
print(target)
