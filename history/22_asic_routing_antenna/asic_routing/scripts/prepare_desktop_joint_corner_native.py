"""Use verified higher-layer clock guides and reroute two complete nets in one source."""
from pathlib import Path
from collections import Counter
import ast,hashlib,json,struct,odb
R=Path('/work/routing'); sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'inputs/desktop_joint_corner_partial.odb'; global_source=R/'runs/global_desktop_joint_corner/final/odb/fault_v_asic_top.odb'
audit=json.loads((R/'reports/desktop_joint_corner_input.json').read_text());assert sha(source)==audit['partial_sha256']
g=json.loads((R/'reports/global_desktop_joint_corner/global_checks.json').read_text());assert g['pass'] and g['total_overflow']==0 and sha(global_source)==g['odb_sha256']
# Reuse the existing byte-level wire and guide validators.
for name,names in [('prepare_cold_corner_reguide.py',{'guide_sig','guides','wires','obstructions'}),('prepare_desktop_checkpoint45.py',{'fixed'})]:
 tree=ast.parse((R/'scripts'/name).read_text(encoding='utf-8-sig'))
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]; assert {n.name for n in nodes}==names
 exec(compile(ast.Module(body=nodes,type_ignores=[]),name,'exec'))
def load(p):
 d=odb.dbDatabase.create();odb.read_db(d,str(p));return d,d.getChip().getBlock()
d,b=load(source); gd,gb=load(global_source)
before=fixed(b); assert before==fixed(gb) and obstructions(b)==obstructions(gb)
original=wires(b);assert len(original)==audit['retained_wire_count']==41314
retained=original
assert all(not b.findNet(name).getWire() for name in audit['cleared_whole_nets'] if b.findNet(name))
expected=guides(gb); count=0
for net in b.getNets():
 for q in list(net.getGuides()):odb.dbGuide.destroy(q)
 for layer,via,box,congested,connected,jumper in expected[net.getName()]:
  l=d.getTech().findLayer(layer);v=d.getTech().findLayer(via);assert l and v
  q=odb.dbGuide_create(net,l,v,odb.Rect(*box),congested);assert q
  q.setIsConnectedToTerm(connected);q.setIsJumper(jumper);count+=1
assert guides(b)==expected and wires(b)==retained and fixed(b)==before
assert all(expected[name] for name in audit['cleared_whole_nets'] if b.findNet(name) and len(b.findNet(name).getITerms())+len(b.findNet(name).getBTerms())>=2)
out=R/'inputs/desktop_joint_corner_native.odb'; assert not out.exists(); odb.write_db(d,str(out))
state={'odb':'/work/routing/inputs/desktop_joint_corner_native.odb','metrics':{}}
for key in ['nl','pnl','sdc','json_h','vh']:
 files=list((R/'runs/global_desktop_joint_corner/final'/key).glob('*')); assert len(files)==1
 state[key]='/work/routing/'+files[0].relative_to(R).as_posix()
(R/'desktop_joint_corner_native_state.json').write_text(json.dumps(state,indent=2)+'\n')
assert sha(source)==audit['partial_sha256'] and sha(global_source)==g['odb_sha256']
record={'accepted':False,'source':source.relative_to(R).as_posix(),'source_sha256':sha(source),'derived_sha256':sha(out),'global_run':'global_desktop_joint_corner','global_source_sha256':sha(global_source),'global_overflow':0,'cleared_whole_nets':audit['cleared_whole_nets'],'retained_wire_count':len(retained),'retained_wires_exact_opcode_data_match':True,'cells_graph_pg_unchanged_from_electrical_proposal':True,'all_guides_match_actual_zero_overflow_source':True,'guide_count':count,'electrical_proposal':'reports/desktop_joint_corner_input.json','scope':'Joint local-neighborhood reroute after measured electrical/hold ECO, preserving 41314 unaffected native wires. All guides and original macro/technology obstructions exactly match new zero-overflow global parent. Actual routing/RC/STA and calibrated independent DRC still required.'}
(R/'reports/desktop_joint_corner_native_input.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2),flush=True)
