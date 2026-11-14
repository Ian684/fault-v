"""Derive a metadata-only candidate from the immutable accepted routing database."""
from pathlib import Path
from collections import Counter
import ast, hashlib, json, struct
import odb

R=Path('/work/routing')
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'runs/routed_desktop_residual_four_20261026_174504/final/odb/fault_v_asic_top.odb'
assert sha(source)=='196e8c9b7d74a0000d8b0869b9b6d2cc9ad7a73b7b44b6a3f389ce25d758cc16'
model=json.loads((R/'reports/antenna_model/sram_antenna_model.json').read_text())
assert model['pass'] and model['geometry_and_pin_directions_unchanged']
for p,h in model['files_sha256'].items():
    assert sha(R.parent/p.replace('\\','/'))==h, p
for name,names in [('prepare_cold_corner_reguide.py',{'guide_sig','guides','wires','obstructions'}),('prepare_desktop_checkpoint45.py',{'fixed'})]:
    tree=ast.parse((R/'scripts'/name).read_text(encoding='utf-8-sig'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),name,'exec'))
d=odb.dbDatabase.create(); odb.read_db(d,str(source)); b=d.getChip().getBlock()
before=(fixed(b),wires(b),guides(b),obstructions(b))
masters={i.getMaster().getName():i.getMaster() for i in b.getInsts() if i.getMaster().isBlock()}
assert len(masters)==1
master=next(iter(masters.values()))
assert master.getName()=='sky130_sram_2kbyte_1rw1r_32x512_8'
for pin,areas in model['pin_areas'].items():
    mt=master.findMTerm(pin); assert mt
    if 'gate_area_um2' in areas:
        assert not mt.hasDefaultAntennaModel(),pin
        mt.createDefaultAntennaModel().addGateAreaEntry(float(areas['gate_area_um2']))
    else:
        mt.addDiffAreaEntry(float(areas['diff_area_um2']))
assert (fixed(b),wires(b),guides(b),obstructions(b))==before
out=R/'inputs/antenna_model_validated.odb'; assert not out.exists()
odb.write_db(d,str(out))
final=source.parents[1]
state={'odb':'/work/routing/inputs/antenna_model_validated.odb','metrics':{}}
for key in ['nl','pnl','sdc','json_h','vh']:
    paths=list((final/key).glob('*')); assert len(paths)==1,(key,paths)
    state[key]='/work/routing/'+paths[0].relative_to(R).as_posix()
(R/'antenna_model_state.json').write_text(json.dumps(state,indent=2)+'\n')
c=json.loads((R/'config_routed_desktop_residual_four_20261026_174504.json').read_text())
c['DRT_ANTENNA_REPAIR_ITERS']=5
c['DRT_ANTENNA_REPAIR_DIODE_ONLY']=True
c['DRT_ANTENNA_REPAIR_MARGIN']=10
c['MACROS'][master.getName()]['lef']=['dir::macros/'+master.getName()+'.antenna.lef']
(R/'config_antenna_closure.json').write_text(json.dumps(c,indent=2)+'\n')
receipt={'pass':True,'accepted':False,'source':str(source.relative_to(R)),'source_sha256':sha(source),'derived':str(out.relative_to(R)),'derived_sha256':sha(out),'routing_cells_graph_PG_guides_obstructions_unchanged':True,'routed_nets':len(before[1]),'model_receipt':'reports/antenna_model/sram_antenna_model.json'}
(R/'reports/antenna_model/candidate_input.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
