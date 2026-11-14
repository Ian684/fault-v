"""Negative control: dbFill must affect extraction before post-fill PEX can be claimed."""
from pathlib import Path
from openroad import Tech, Design
import ast, hashlib, json, struct, odb

C=Path('/work/week25_closure');R=Path('/work/routing')
source=C/'runs/probe_rc_a/1-openroad-fillinsertion/fault_v_asic_top.odb'
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','obstructions'})]:
    tree=ast.parse((R/'scripts'/file).read_text())
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
t=Tech();d=Design(t);d.readDb(str(source));db=d.getDb();b=db.getChip().getBlock()
before=(fixed(b),wires(b),obstructions(b));assert len(list(b.getFills()))==0
die=b.getDieArea();created=[]
# Deliberately enormous, unconnected rectangles are a sensitivity control, not a legal layout.
for layername in ('met1','met2','met3','met4','met5'):
    layer=db.getTech().findLayer(layername);assert layer is not None
    fill=odb.dbFill_create(b,False,0,layer,die.xMin()+1000,die.yMin()+1000,die.xMax()-1000,die.yMax()-1000)
    assert fill is not None;created.append(layername)
assert len(list(b.getFills()))==5 and (fixed(b),wires(b),obstructions(b))==before
target=C/'inputs/rcx_fill_control.odb';assert not target.exists();odb.write_db(db,str(target))
state=json.loads((C/'runs/probe_rc_a/3-openroad-rcx/state_in.json').read_text())
state.update(odb=str(target),metrics={});(C/'fill_rcx_state.json').write_text(json.dumps(state,indent=2)+'\n')
cfg=json.loads((C/'config_probe_rc.json').read_text());cfg['meta']={'version':2,'flow':['OpenROAD.RCX']}
resolved=json.loads((C/'runs/probe_rc_a/resolved.json').read_text())
cfg['RCX_RULESETS']={k:v for k,v in resolved['RCX_RULESETS'].items() if k.startswith('nom')}
assert len(cfg['RCX_RULESETS'])==1
(C/'config_fill_rcx.json').write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/fill_rcx_control_input.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'control_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'added_dbFill_layers':created,'all_cells_nets_regular_wires_PG_unchanged':True,'control_is_manufacturable':False,'scope':'Extraction sensitivity only. Deliberately illegal giant dummy rectangles must never be promoted.'},indent=2)+'\n')
print('RCX dummy-fill sensitivity control prepared',flush=True)
