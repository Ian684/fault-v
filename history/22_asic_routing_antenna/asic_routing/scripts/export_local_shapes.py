from pathlib import Path
from collections import Counter
import odb,json,hashlib
R=Path("/work/routing")
source=R/"runs/routed_final/1-openroad-detailedrouting/drt_iter52.odb"
d=odb.dbDatabase.create();odb.read_db(d,str(source))
b=d.getChip().getBlock();tech=d.getTech()
# shortcut: these two standard-width, uncolored nets only; extend codec checks before reuse.
def primitives(w):
 dec=odb.dbWireDecoder();dec.begin(w);layer=None;prev=None;ext=None;nodes={};items=[];edges={}
 while True:
  op=dec.next()
  if op==dec.END_DECODE:break
  if op==dec.PATH:
   layer=dec.getLayer();prev=None;ext=None
   assert str(dec.getWireType())=="ROUTED"
  elif op==dec.JUNCTION:
   prev,layer,ext=nodes[dec.getJunctionValue()]
  elif op in [dec.POINT,dec.POINT_EXT]:
   p=tuple((dec.getPoint_ext() if op==dec.POINT_EXT else dec.getPoint())[:2])
   ex=dec.getPoint_ext()[2] if op==dec.POINT_EXT else layer.getWidth()//2
   jid=dec.getJunctionId()
   if prev is not None and p!=prev:
    a,z,ae,ze=(prev,p,ext,ex) if prev<p else (p,prev,ex,ext)
    item=("S",layer.getName(),*a,*z,ae,ze)
    items.append(item);edges[(layer.getName(),a,z)]=jid
   prev=p;ext=ex;nodes[jid]=(p,layer,ext)
  elif op in [dec.TECH_VIA,dec.VIA]:
   via=dec.getTechVia() if op==dec.TECH_VIA else dec.getVia()
   items.append(("T" if op==dec.TECH_VIA else "V",via.getName(),*prev))
   layer=dec.getLayer();ext=layer.getWidth()//2;nodes[dec.getJunctionId()]=(prev,layer,ext)
  elif op==dec.RECT:
   x1,y1,x2,y2=[w.getData(dec.getJunctionId()+i) for i in range(4)];items.append(("R",layer.getName(),prev[0]+x1,prev[1]+y1,prev[0]+x2,prev[1]+y2))
  else:
   assert op in [dec.ITERM,dec.BTERM],("Unsupported wire opcode",op)
 return Counter(items),edges
def normalize_routes(w):
 dec=odb.dbWireDecoder();dec.begin(w);records=[]
 while True:
  op=dec.next()
  if op==dec.END_DECODE:break
  if op in [dec.PATH,dec.JUNCTION]:records.append(("path",dec.getLayer()))
  elif op==dec.POINT:records.append(("point",tuple(dec.getPoint())))
  elif op==dec.POINT_EXT:records.append(("ext",tuple(dec.getPoint_ext())))
  elif op==dec.TECH_VIA:records.append(("tech",dec.getTechVia()))
  elif op==dec.VIA:records.append(("via",dec.getVia()))
  elif op==dec.RECT:records.append(("rect",tuple(w.getData(dec.getJunctionId()+i) for i in range(4))))
  elif op==dec.ITERM:records.append(("iterm",dec.getITerm()))
  elif op==dec.BTERM:records.append(("bterm",dec.getBTerm()))
  else:raise AssertionError(("Unsupported normalization opcode",op))
 enc=odb.dbWireEncoder();enc.begin(w)
 for op,value in records:
  if op=="path":enc.newPath(value,"ROUTED")
  elif op=="point":enc.addPoint(*value)
  elif op=="ext":enc.addPoint(*value,0)
  elif op=="tech":enc.addTechVia(value)
  elif op=="via":enc.addVia(value)
  elif op=="rect":enc.addRect(*value)
  elif op=="iterm":enc.addITerm(value)
  elif op=="bterm":enc.addBTerm(value)
 enc.end()
def restore_patches(w,before):
 after,_=primitives(w)
 missing=before-after
 patches=[k for k in missing.elements() if k[0]=="R"]
 if patches:
  enc=odb.dbWireEncoder();enc.append(w)
  for _,layer,x1,y1,x2,y2 in patches:
   enc.newPath(tech.findLayer(layer),"ROUTED");enc.addPoint(x1,y1);enc.addRect(0,0,x2-x1,y2-y1)
  enc.end()
def choose_via(lo,hi):
 candidates=[v for v in tech.getVias() if v.getBottomLayer().getName()==lo and v.getTopLayer().getName()==hi]
 assert candidates,(lo,hi)
 def score(v):
  boxes=[z for z in v.getBoxes() if z.getTechLayer().getName()==lo]
  return max(z.yMax() for z in boxes)-min(z.yMin() for z in boxes),sum((z.xMax()-z.xMin())*(z.yMax()-z.yMin()) for z in boxes),v.getName()
 return min(candidates,key=score)

region=(1595000,550000,1645000,620000)
shapes=[]
def add(layer,box,net):
 x1,y1,x2,y2=box
 if x2>=region[0] and x1<=region[2] and y2>=region[1] and y1<=region[3]:
  shapes.append([layer,x1,y1,x2,y2,net])
def rect(q):return [q.xMin(),q.yMin(),q.xMax(),q.yMax()]
for net in b.getNets():
 name=net.getName();w=net.getWire()
 if w:
  try:ps,_=primitives(w)
  except AssertionError:continue
  for v in ps:
   if v[0]=='S':
    _,l,x1,y1,x2,y2,e1,e2=v;half=tech.findLayer(l).getWidth()//2
    if x1==x2:add(l,[x1-half,y1-e1,x2+half,y2+e2],name)
    else:add(l,[x1-e1,y1-half,x2+e2,y2+half],name)
   elif v[0]=='R':add(v[1],v[2:6],name)
   elif v[0] in ['T','V']:
    _,vn,x,y=v
    if not(region[0]-2000<x<region[2]+2000 and region[1]-2000<y<region[3]+2000):continue
    via=tech.findVia(vn) if v[0]=='T' else b.findVia(vn)
    for q in via.getBoxes():
     add(q.getTechLayer().getName(),[q.xMin()+x,q.yMin()+y,q.xMax()+x,q.yMax()+y],name)
 for sw in net.getSWires():
  for q in sw.getWires():
   if not q.isVia():add(q.getTechLayer().getName(),rect(q),name)
for inst in b.getInsts():
 q=inst.getBBox()
 if q.xMax()<region[0] or q.xMin()>region[2] or q.yMax()<region[1] or q.yMin()>region[3]:continue
 for it in inst.getITerms():
  for l,q in it.getGeometries():add(l.getName(),rect(q),it.getNet().getName() if it.getNet() else '@pin')
 # Local standard-cell obstructions are fixed geometry too.
 orient=str(inst.getOrient());ox,oy=inst.getLocation();mw=inst.getMaster().getWidth();mh=inst.getMaster().getHeight()
 assert orient in ['R0','MX','MY','R180'],orient
 for q in inst.getMaster().getObstructions():
  x1,y1,x2,y2=q.xMin(),q.yMin(),q.xMax(),q.yMax()
  if orient in ['MY','R180']:x1,x2=mw-x2,mw-x1
  if orient in ['MX','R180']:y1,y2=mh-y2,mh-y1
  add(q.getTechLayer().getName(),[ox+x1,oy+y1,ox+x2,oy+y2],'@obs')
vs=[]
for v in tech.getVias():
 if v.getBottomLayer().getName() in ['met1','met2','met3']:
  vs.append({'name':v.getName(),'lo':v.getBottomLayer().getName(),'hi':v.getTopLayer().getName(),'boxes':[[q.getTechLayer().getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax()] for q in v.getBoxes()]})
(R/'reports/manual_search/local_shapes.json').write_text(json.dumps({'region':region,'shapes':shapes,'vias':vs}))
print('LOCAL_SHAPES',len(shapes),flush=True)
