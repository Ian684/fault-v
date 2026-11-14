from pathlib import Path
import json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load
C=Path('/work/week25_closure');db,b=load('/runtime_final/focus_pg.odb')
record=json.loads((C/'reports/antenna_stub_full_targets.json').read_text())
targets={'ANTENNA_7554':('_10658_','wire6040','A'),'ANTENNA_7568':('net6033','_39369_','B1')}
for row in record['diodes']:
    if row['diode'] not in targets:continue
    net,inst,pin=targets[row['diode']];assert row['net']==net
    i=b.findInst(inst);p=i.findITerm(pin);assert p.getNet().getName()==net
    x,y=i.getLocation();choices=[]
    for a in p.getPrefAccessPoints():
        layer=a.getLayer().getName();px,py=a.getPoint();gx,gy=x+px,y+py
        assert layer in ('li1','met1','met2')
        assert any(l.getName()==layer and z.xMin()<=gx<=z.xMax() and z.yMin()<=gy<=z.yMax() for l,z in p.getGeometries())
        cost=min(abs(gx-ax)+abs(gy-ay)+500*abs((0 if al=='li1' else int(al[-1]))-(0 if layer=='li1' else int(layer[-1]))) for ax,ay,al in row['access_points'])
        choices.append((cost,layer,gx,gy,('VIOLATING_GATE_NATIVE_AP',inst,pin)))
    assert choices;row['closest_preserved_segments']=sorted(choices)
record['scope']='Two residual M2 antenna violators target the actual offending gate native AP; their new paths are limited to LI1/M1/M2. Other checked branches are replayed unchanged.'
out=C/'reports/antenna_stub_two_gate_targets.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n')
print('TWO_VIOLATING_GATE_TARGETS',[(r['diode'],r['closest_preserved_segments']) for r in record['diodes'] if r['diode'] in targets],flush=True)
