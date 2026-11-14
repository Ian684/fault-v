"""Finite local jumper search on one coherent native checkpoint; strict native DRC oracle."""
from pathlib import Path
from collections import Counter
from openroad import Tech,Design
import ast,odb,json,hashlib,struct,re,os
R=Path('/work/routing');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof=json.loads((R/'reports/desktop_bridge_source42.json').read_text(encoding='utf-8'));source=R/proof['frozen_copy'];assert sha(source)==proof['source_sha256']
raw=(R/proof['native_report']).read_text(encoding='utf-8')
pattern=r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = \(([-0-9.]+), ([-0-9.]+)\) - \(([-0-9.]+), ([-0-9.]+)\) on Layer ([^\n]+)'
def parse(text):
 rows=[]
 for m in re.finditer(pattern,text):
  kind,src,x1,y1,x2,y2,layer=m.groups();src=' '.join(sorted(re.findall(r'(?:net|inst):\S+',src))) if kind=='Short' else src.strip();rows.append((kind,src,tuple(round(float(v)*1000) for v in [x1,y1,x2,y2]),layer.strip()))
 assert len(rows)==text.count('violation type:'),'Unparsed native markers';return Counter(rows)
markers=parse(raw);assert sum(markers.values())==3 and all(k[0]=='Short' and k[3]=='met1' and len(re.findall(r'net:(\S+)',k[1]))==2 for k in markers)
attempt=os.environ.get('BRIDGE_ATTEMPT','one');assert re.fullmatch(r'[A-Za-z0-9_]+',attempt);folder=R/'reports'/('desktop_bridge_attempt_'+attempt);folder.mkdir(exist_ok=False)
t=Tech();design=Design(t);design.readDb(str(source));d=design.getDb();b=d.getChip().getBlock();tech=d.getTech();assert tech.getManufacturingGrid()==5
def load(file,names):
 tree=ast.parse((R/'scripts'/file).read_text(encoding='utf-8-sig'));nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names;exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'),globals())
load('prepare_desktop_checkpoint45.py',{'fixed'});load('prepare_cold_corner_reguide.py',{'wires','obstructions','guides','guide_sig'});load('search_manual_eco.py',{'primitives','normalize_routes','restore_patches'})
identity=fixed(b);obs=obstructions(b);original_wires=wires(b);assert len(original_wires)==41337
via_names={frozenset(['met1','met2']):'M1M2_PR',frozenset(['met2','met3']):'M2M3_PR'}
assert all(tech.findVia(v) for v in via_names.values());design.evalTclString('set_thread_count 4');trial=0;touched=set();accepted=[]
def drc(box,label):
 design.getTritonRoute().clearDesign();p=folder/(label+'.rpt');design.evalTclString('drt::check_drc -box {'+' '.join(map(str,box))+'} -output_file '+str(p)+' -marker_name LocalBridge');return parse(p.read_text(encoding='utf-8'))
def ends(s):return tuple(s[2:4]),tuple(s[4:6])
def seg(layer,a,z):
 a,z=sorted([a,z]);half=tech.findLayer(layer).getWidth()//2;return ('S',layer,*a,*z,half,half)
def valid(s):return s[0]=='S' and s[1]=='met1' and s[-2:]==(70,70)
def plans(p,net,cx,cy):
 candidates=[s for s in p if valid(s) and min(s[2],s[4])-70<=cx<=max(s[2],s[4])+70 and min(s[3],s[5])-70<=cy<=max(s[3],s[5])+70 and p[s]==1]
 # Prefer vertical crossings, then longer edges.
 candidates.sort(key=lambda s:(s[2]!=s[4],-abs(s[4]-s[2])-abs(s[5]-s[3])))
 for s in candidates:
  a,z=ends(s);length=abs(z[0]-a[0])+abs(z[1]-a[1]);vertical=a[0]==z[0]
  if 400<=length<=3000:
   yield [s],[('met1',a),('met2',a),('met2',z),('met1',z)],'direct_met2'
  if vertical and a[1]>=cy-3500 and z[1]<=cy+3500:
   hs=[]
   for point in [a,z]:hs.append([q for q in p if valid(q) and q!=s and q[3]==q[5] and point in ends(q) and p[q]==1])
   if len(hs[0])==len(hs[1])==1:
    safe=True
    for point in [a,z]:
     degree=sum(v for q,v in p.items() if q[0]=='S' and q[1]=='met1' and point in ends(q))
     if degree!=2 or any(q[0] in ['T','V'] and tuple(q[2:4])==point for q in p):safe=False
     for term in net.getITerms():
      if any(l.getName()=='met1' and box.xMin()<=point[0]<=box.xMax() and box.yMin()<=point[1]<=box.yMax() for l,box in term.getGeometries()):safe=False
    if safe:
     h1,h2=hs[0][0],hs[1][0];outer1=next(q for q in ends(h1) if q!=a);outer2=next(q for q in ends(h2) if q!=z)
     for dx in [0,-460,460,-920,920,-1380,1380,-230,230,-690,690,-1150,1150]:
      x=a[0]+dx
      yield [h1,s,h2],[('met1',outer1),('met1',(x,a[1])),('met2',(x,a[1])),('met2',(x,z[1])),('met1',(x,z[1])),('met1',outer2)],'shifted_vertical_met2'
  axis=1 if vertical else 0;lo=a[axis];hi=z[axis];center=cy if vertical else cx
  for radius in [460,680,920,1380]:
   low=max(lo,round((center-radius)/5)*5);high=min(hi,round((center+radius)/5)*5)
   if high-low<400:continue
   p1=(a[0],low) if vertical else (low,a[1]);p2=(a[0],high) if vertical else (high,a[1])
   yield [s],[('met1',a),('met1',p1),('met2',p1),('met2',p2),('met1',p2),('met1',z)],'trimmed_met2'
   if not vertical and high-low>=680:
    base=round((a[1]-340)/680)*680+340
    for dy in [0,-680,680,-1360,1360]:
     y=base+dy
     yield [s],[('met1',a),('met1',p1),('met2',p1),('met2',(p1[0],y)),('met3',(p1[0],y)),('met3',(p2[0],y)),('met2',(p2[0],y)),('met2',p2),('met1',p2),('met1',z)],'local_met3_jumper'
def flat_encode(w,p):
 e=odb.dbWireEncoder();e.begin(w)
 for q in p.elements():
  if q[0]=='S':
   _,l,x1,y1,x2,y2,a,z=q;e.newPath(tech.findLayer(l),'ROUTED');e.addPoint(x1,y1,a);e.addPoint(x2,y2,z)
  elif q[0] in ['T','V']:
   _,name,x,y=q;v=tech.findVia(name) if q[0]=='T' else b.findVia(name);assert v;e.newPath(v.getBottomLayer(),'ROUTED');e.addPoint(x,y)
   if q[0]=='T':e.addTechVia(v)
   else:e.addVia(v)
  elif q[0]=='R':
   _,l,x1,y1,x2,y2=q;e.newPath(tech.findLayer(l),'ROUTED');e.addPoint(x1,y1);e.addRect(0,0,x2-x1,y2-y1)
  else:raise AssertionError(q)
 e.end()
def pins_connected(p,net):
 metal={'li1','met1','met2','met3','met4','met5'};nodes=[]
 for q in p.elements():
  if q[0]=='S':
   _,l,x1,y1,x2,y2,e1,e2=q;half=tech.findLayer(l).getWidth()//2
   z=(x1-half,y1-e1,x2+half,y2+e2) if x1==x2 else (x1-e1,y1-half,x2+e2,y2+half);nodes.append([(l,z)])
  elif q[0]=='R':nodes.append([(q[1],tuple(q[2:6]))])
  elif q[0] in ['T','V']:
   _,name,x,y=q;via=tech.findVia(name) if q[0]=='T' else b.findVia(name);nodes.append([(box.getTechLayer().getName(),(box.xMin()+x,box.yMin()+y,box.xMax()+x,box.yMax()+y)) for box in via.getBoxes() if box.getTechLayer().getName() in metal])
 pins=[]
 for term in net.getITerms():
  if str(term.getMTerm().getSigType()) in ['POWER','GROUND']:continue
  shapes=[(l.getName(),(box.xMin(),box.yMin(),box.xMax(),box.yMax())) for l,box in term.getGeometries() if l.getName() in metal];assert shapes;pins.append(len(nodes));nodes.append(shapes)
 assert not list(net.getBTerms()),'Boundary-pin connectivity needs explicit support'
 parent=list(range(len(nodes)))
 def root(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 grouped={}
 for i,shapes in enumerate(nodes):
  for layer,z in shapes:grouped.setdefault(layer,[]).append((i,z))
 for values in grouped.values():
  for a,(i,z) in enumerate(values):
   for j,w in values[a+1:]:
    if z[0]<=w[2] and z[2]>=w[0] and z[1]<=w[3] and z[3]>=w[1]:parent[root(i)]=root(j)
 return bool(pins) and len({root(i) for i in pins})==1
def apply(w,original,cuts,pts):
 pts=[q for i,q in enumerate(pts) if i==0 or q!=pts[i-1]];assert all(v%5==0 for layer,p in pts for v in p);expected=original.copy()
 for q in cuts:assert expected[q]==1;expected.subtract({q:1})
 for (l,a),(m,z) in zip(pts,pts[1:]):
  if l==m:assert a[0]==z[0] or a[1]==z[1];expected.update({seg(l,a,z):1})
  else:assert a==z;expected.update({('T',via_names[frozenset([l,m])],*a):1})
 expected=+expected;flat_encode(w,expected);assert primitives(w)[0]==expected,'Unexpected explicit path geometry'

for marker in markers:
 pair=re.findall(r'net:(\S+)',marker[1]);x1,y1,x2,y2=marker[2];cx=round(((x1+x2)/2)/5)*5;cy=round(((y1+y2)/2)/5)*5;box=[cx-5000,cy-5000,cx+5000,cy+5000];baseline=drc(box,'pair_'+str(len(accepted))+'_before')
 target=lambda k:k[0]=='Short' and set(re.findall(r'net:(\S+)',k[1]))==set(pair) and k[3]=='met1'
 assert any(target(k) for k in baseline),'Expected actual short absent from local context'
 found=False
 for name in pair:
  net=b.findNet(name);assert net and str(net.getSigType())=='SIGNAL';w=net.getWire();original,_=primitives(w);assert pins_connected(original,net),'Source signal pins are disconnected';flat_encode(w,original);assert primitives(w)[0]==original;touched.add(name)
  seen=set()
  for cuts,pts,mode in plans(original,net,cx,cy):
   token=str((cuts,pts))
   if token in seen:continue
   seen.add(token);trial+=1;assert trial<=500,'Finite search budget exhausted'
   flat_encode(w,original);assert primitives(w)[0]==original
   apply(w,original,cuts,pts)
   if not pins_connected(primitives(w)[0],net):print('TRIAL',trial,name,mode,'rejected_pin_connectivity',flush=True);continue
   after=drc(box,'trial_'+str(trial))
   print('TRIAL',trial,name,mode,sum(after.values()),flush=True)
   if not (after-baseline) and not any(target(k) for k in after):
    accepted.append({'pair':pair,'changed_net':name,'mode':mode,'removed_segments':cuts,'replacement_path':pts,'before_local_markers':sum(baseline.values()),'after_local_markers':sum(after.values()),'local_report':'reports/'+folder.name+'/trial_'+str(trial)+'.rpt'});found=True;print('BRIDGE_ACCEPTED',json.dumps(accepted[-1]),flush=True);break
  if found:break
  flat_encode(w,original);assert primitives(w)[0]==original
 assert found,('No validated local bridge',pair)
assert fixed(b)==identity and obstructions(b)==obs
for name in touched:assert pins_connected(primitives(b.findNet(name).getWire())[0],b.findNet(name))
for marker in markers:
 x1,y1,x2,y2=marker[2];box=[x1-5000,y1-5000,x2+5000,y2+5000];rows=drc(box,'combined_'+str(x1));assert not rows,'Combined modified area must be clean'
global_source=R/'runs/global_desktop_joint_corner/final/odb/fault_v_asic_top.odb';gc=json.loads((R/'reports/global_desktop_joint_corner/global_checks.json').read_text(encoding='utf-8'));assert gc['pass'] and gc['total_overflow']==0 and sha(global_source)==gc['odb_sha256']
gd=odb.dbDatabase.create();odb.read_db(gd,str(global_source));gb=gd.getChip().getBlock();assert fixed(b)==fixed(gb) and obstructions(b)==obstructions(gb)
expected=guides(gb)
for net in b.getNets():
 for q in list(net.getGuides()):odb.dbGuide.destroy(q)
 for layer,via,bb,congested,connected,jumper in expected[net.getName()]:
  q=odb.dbGuide_create(net,d.getTech().findLayer(layer),d.getTech().findLayer(via),odb.Rect(*bb),congested);assert q;q.setIsConnectedToTerm(connected);q.setIsJumper(jumper)
assert guides(b)==expected and fixed(b)==identity and obstructions(b)==obs
after_wires=wires(b);changed={n for n in original_wires if original_wires[n]!=after_wires[n]};assert changed<=touched and len(after_wires)==41337
out=R/'inputs/desktop_local_bridge_native.odb';receipt=R/'reports/desktop_local_bridge_input.json';assert not out.exists() and not receipt.exists();state={'odb':str(out),'metrics':{}}
for key in ['nl','pnl','sdc','json_h','vh']:
 files=list((R/'runs/global_desktop_joint_corner/final'/key).glob('*'));assert len(files)==1;state[key]=str(files[0])
odb.write_db(d,str(out));(R/'desktop_local_bridge_state.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
record={'accepted':False,'source':str(source.relative_to(R)),'source_sha256':sha(source),'derived_sha256':sha(out),'global_run':'global_desktop_joint_corner','global_source_sha256':sha(global_source),'global_overflow':0,'source_native_drc':3,'accepted_local_bridges':accepted,'trial_count':trial,'changed_wire_encodings':sorted(changed),'retained_wire_count':41337-len(changed),'cells_graph_pg_obstructions_unchanged':True,'modified_signal_pin_geometry_connected':True,'explicit_path_encoder_noop_native_control_passed':True,'all_guides_match_actual_zero_overflow_source':True,'scope':'One coherent native checkpoint. Finite local native-DRC-validated metal2/3 jumpers replace only explicit mid-wire segments. Combined modified boxes clean; no rules, pins, cells, functional graph or power changes. Full native routing, independent full DRC, freshRC/STA/phase/PG gates remain required.'};receipt.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');assert sha(source)==proof['source_sha256'];print(json.dumps(record,indent=2),flush=True)
