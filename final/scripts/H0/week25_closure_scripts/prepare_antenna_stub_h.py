from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs_g.py').read_text().replace('antenna_stubs_g','antenna_stubs_h').replace('reports/antenna_stubs_f/result.json','reports/antenna_stubs_g/incomplete.json').replace("if row['net'] in ('_10658_','net6033'):continue","if row['net']=='net6033':continue")
code=code.replace(')-15000',')-25000').replace(')+15000',')+25000')
marker="exec(compile(source.replace('time.monotonic()-began>180','time.monotonic()-began>35'),'bounded_existing_local_planner','exec'))"
assert code.count(marker)==1
prefix="source=source.replace('range((loX//50)*50,hiX+1,50)','range((loX//100)*100,hiX+1,100)').replace('range((loY//50)*50,hiY+1,50)','range((loY//100)*100,hiY+1,100)').replace('count>600000','count>2000000')\n"
code=code.replace(marker,prefix+marker.replace('began>35','began>120'))
p=C/'scripts/append_antenna_stubs_h.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('ONE_REMAINING_LOW_LAYER_STUB_H_PREPARED')
