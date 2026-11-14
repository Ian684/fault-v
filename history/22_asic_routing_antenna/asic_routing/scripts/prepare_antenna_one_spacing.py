"""Move one wire bend away from the SRAM obstruction; keep all other routes exact."""
from pathlib import Path
from collections import Counter
from openroad import Tech,Design
import ast,hashlib,json,os,re,struct,odb
R=Path('/work/routing');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'inputs/antenna_spacing_source59.odb'
assert sha(source)=='49b0ea2ed38970fac305dbe616d6d8aec3dd423ccee8ceccd0ea3d7281bdcdbe'
attempt=os.environ.get('SPACING_ATTEMPT','01');assert re.fullmatch('[A-Za-z0-9_]+',attempt)
folder=R/'reports/antenna_model/debug_spacing_20261029'/('native_search_'+attempt);folder.mkdir(exist_ok=False)
pattern=r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = \(([-0-9.]+), ([-0-9.]+)\) - \(([-0-9.]+), ([-0-9.]+)\) on Layer ([^\n]+)'
def load(file,names):
    tree=ast.parse((R/'scripts'/file).read_text(encoding='utf-8-sig'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'),globals())
load('search_manual_eco.py',{'primitives'})
load('prepare_desktop_checkpoint45.py',{'fixed'})
load('prepare_cold_corner_reguide.py',{'wires','guides','guide_sig','obstructions'})
load('prepare_desktop_local_bridge_flat.py',{'parse','flat_encode','pins_connected'})
# Require the complete changed net, including every metal fragment, to stay connected.
tree=ast.parse((R/'scripts/prepare_desktop_local_bridge_flat.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='pins_connected')
text=ast.unparse(node);needle='len({root(i) for i in pins})';assert text.count(needle)==1
exec(text.replace(needle,'len({root(i) for i in range(len(nodes))})'),globals())
t=Tech();design=Design(t);design.readDb(str(source));d=design.getDb();b=d.getChip().getBlock();tech=d.getTech()
assert tech.getManufacturingGrid()==5 and tech.findLayer('met2').getWidth()==140
identity=fixed(b);old_guides=guides(b);obs=obstructions(b);old_wires=wires(b);assert len(old_wires)==41337
net=b.findNet('net3116');assert net and str(net.getSigType())=='SIGNAL' and net.getNonDefaultRule() is None
w=net.getWire();original=primitives(w)[0];assert pins_connected(original,net)
cuts=[('S','met2',1576190,640220,1582630,640220,70,70),('S','met2',1582630,640220,1582630,640390,70,70),('S','met2',1582630,640390,1583090,640390,70,70)]
assert all(original[q]==1 for q in cuts)
for point in [(1582630,640220),(1582630,640390)]:
    assert sum(count for q,count in original.items() if q[0]=='S' and q[1]=='met2' and point in [q[2:4],q[4:6]])==2
    assert not any(q[0] in ['T','V'] and q[2:4]==point for q in original)
design.evalTclString('set_thread_count 2')
def drc(label):
    p=folder/(label+'.rpt');assert not p.exists();design.getTritonRoute().clearDesign()
    command='drt::check_drc -box {1573000 635000 1589000 646000} -output_file '+str(p)+' -marker_name SpacingECO'
    status=str(design.evalTclString('set spacing_status [catch {'+command+'} spacing_result]; set spacing_status')).strip()
    assert status=='0' and p.exists(),('Native DRC failed',status)
    return parse(p.read_text())
baseline=drc('source_negative');assert sum(baseline.values())==1
assert all(q[0]=='Metal Spacing' and q[3]=='met2' and 'net:net3116' in q[1] for q in baseline)
flat_encode(w,original);assert primitives(w)[0]==original and pins_connected(original,net)
assert drc('noop_control')==baseline,'Geometry-equivalent encoder changed native DRC'
def length(p):return sum((abs(q[4]-q[2])+abs(q[5]-q[3]))*count for q,count in p.items() if q[0]=='S')
chosen=None;trials=[]
for x in [1582790,1582800,1582780,1582810,1582770,1582820]:
    expected=original.copy()
    for q in cuts:expected.subtract({q:1})
    pts=[(1576190,640220),(x,640220),(x,640390),(1583090,640390)]
    pts=[q for k,q in enumerate(pts) if k==0 or q!=pts[k-1]]
    for a,z in zip(pts,pts[1:]):
        assert all(v%5==0 for v in (*a,*z)) and (a[0]==z[0] or a[1]==z[1])
        a,z=sorted([a,z]);expected.update({('S','met2',*a,*z,70,70):1})
    expected=+expected;flat_encode(w,expected);assert primitives(w)[0]==expected and pins_connected(expected,net)
    assert length(expected)==length(original) and Counter({q:v for q,v in expected.items() if q[0]!='S'})==Counter({q:v for q,v in original.items() if q[0]!='S'})
    rows=drc('shift_'+str(x));trials.append({'bend_x_dbu':x,'native_local_DRC':sum(rows.values())})
    print('SPACING_TRIAL',x,sum(rows.values()),flush=True)
    if not rows:chosen={'bend_x_dbu':x,'removed':cuts,'replacement_path_dbu':pts};break
assert chosen,'No locally clean bend shift; source unchanged'
assert fixed(b)==identity and guides(b)==old_guides and obstructions(b)==obs
after=wires(b);assert set(after)==set(old_wires) and {n for n in after if after[n]!=old_wires[n]}=={'net3116'}
assert pins_connected(primitives(w)[0],net) and not drc('combined')
target=R/'inputs/antenna_spacing_native.odb';assert not target.exists();odb.write_db(d,str(target));assert sha(source)=='49b0ea2ed38970fac305dbe616d6d8aec3dd423ccee8ceccd0ea3d7281bdcdbe'
s=json.loads((R/'antenna_both8_state.json').read_text());s['odb']='/work/routing/inputs/antenna_spacing_native.odb';state=R/'antenna_spacing_state.json';assert not state.exists();state.write_text(json.dumps(s,indent=2)+'\n')
a={'pass':True,'accepted':False,'source':source.relative_to(R).as_posix(),'source_sha256':sha(source),'derived':target.relative_to(R).as_posix(),'derived_sha256':sha(target),'source_native_DRC':1,'native_local_DRC':0,'changed_net':'net3116','retained_exact_other_wires':41336,'cells_graph_PG_guides_obstructions_unchanged':True,'complete_changed_net_metal_and_pins_connected':True,'wire_length_unchanged':True,'via_and_patch_geometry_unchanged':True,'native_negative_source_and_noop_controls_pass':True,'chosen':chosen,'bend_shift_um':(chosen['bend_x_dbu']-1582630)/1000,'trials':trials,'global_run':'global_antenna_4319_control_20261028_184048','scope':'One met2 bend shifted within the existing narrow corridor between an unchanged SRAM obstruction and net5547. Whole-chip native routing, antenna, independent DRC, all signal/PG, extracted RC/TT checks and a new delivery remain mandatory.'}
p=R/'reports/antenna_model/debug_spacing_20261029/spacing_input.json';assert not p.exists();p.write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a,indent=2),flush=True)
