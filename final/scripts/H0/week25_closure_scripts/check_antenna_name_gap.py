"""Check a reversible name-only workaround for the pinned antenna inserter's gap bug."""
from pathlib import Path
import json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,fixed,wires
C=Path('/work/week25_closure');db,b=load('/runtime_final/focus_pg.odb')
assert b.findInst('ANTENNA_7502') is None and b.findInst('ANTENNA_7503')
cell=next(i for i in b.getInsts() if 'tapvpwrvgnd' in i.getMaster().getName())
before=fixed(b);old=wires(b);name=cell.getName()
assert hasattr(cell,'rename'),[m for m in dir(cell) if 'name' in m.lower()]
assert cell.rename('ANTENNA_7502') and b.findInst(name) is None
index=1
while b.findInst(f'ANTENNA_{index}'):index+=1
assert index==7554,index
assert cell.rename(name) and fixed(b)==before and wires(b)==old
(C/'reports/antenna_name_gap_workaround.json').write_text(json.dumps({'source_ODB':'/runtime_final/focus_pg.odb','temporary_tap_name':name,'temporary_alias':'ANTENNA_7502','native_first_free_after_temporary_alias':index,'round_trip_fixed_graph_PG_wire_bytes_equal':True,'scope':'No cell or geometry added. Temporarily aliases one existing tap to occupy the gap, ensuring native diode names start after all existing ANTENNA indices. Alias must be restored before any final export.'},indent=2)+'\n')
print('ANTENNA_NAME_GAP_ROUND_TRIP_VERIFIED',name,index,flush=True)
