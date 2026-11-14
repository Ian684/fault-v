from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/plan_remote_corner.py').read_text()
needle="specs=raw['vias'];byactual={v['actual']:v for v in specs};existing=defaultdict(list)";assert code.count(needle)==1
code=code.replace(needle,"byactual={v['actual']:v for v in raw['vias']};specs=[{**v,'name':v['actual']+'@bare','boxes':v['real'],'pad':None} for v in byactual.values()];existing=defaultdict(list)")
code=code.replace('roi=[1570000,624000,1595000,649000]', 'roi=[1570000,624000,1600000,663000]')
needle="for y in (630870,631550,632230,633250,634270,635630,636650):\n    start=(1580330,y,2);end=(1583550,643450,2);path=env['search'](name,start,end)";assert code.count(needle)==1
code=code.replace(needle,"for y,ex,ey in [(631550,1585390,643450),(630870,1585390,643450),(633250,1585390,643450),(630870,1585390,650000),(631550,1585390,655010),(635630,1585390,643450)]:\n    start=(1580330,y,2);end=(ex,ey,2);path=env['search'](name,start,end)")
code=code.replace('remote_corner_plan_a.json','remote_corner_plan_b.json').replace("'read_only':True", "'read_only':True,'M3_minimum_area':'Via-only M3 islands require a separately checked legal landing patch; natural M3 wire components need no unconditional symmetric pad.'")
p=C/'scripts/plan_remote_corner_b.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('REMOTE_B_USES_EXISTING_UPPER_NATIVE_CONNECTIONS')
