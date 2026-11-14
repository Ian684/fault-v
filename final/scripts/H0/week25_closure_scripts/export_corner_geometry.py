from pathlib import Path
import json,sys
from openroad import Tech,Design
sys.path.insert(0,'/work/routing/scripts')
sys.path.insert(0,'/work/week25_closure/scripts')
C=Path('/work/week25_closure');code=(C/'scripts/native_metal_planner_l.py').read_text()
needle="    print('UPPER_OBSTACLES_READY',len(cache),'via options',len(specs),flush=True)";assert code.count(needle)==1
code=code.replace(needle,needle+"\n    (out/'obstacles.json').write_text(__import__('json').dumps({'bounds':bounds,'shapes':cache,'vias':specs,'target_primitives':list(original.elements())})+'\\n')\n    return None")
env={};exec(compile(code,'read_only_corner_geometry_export','exec'),env)
t=Tech();design=Design(t);design.readDb('/runtime_final/native_group_c.odb');db=design.getDb();b=db.getChip().getBlock();out=C/'reports/native_corner_geometry';out.mkdir(exist_ok=False)
env['repair_corner'](design,db,b,out,None,None)
print('NATIVE_CORNER_GEOMETRY_EXPORTED',str(out/'obstacles.json'),flush=True)
