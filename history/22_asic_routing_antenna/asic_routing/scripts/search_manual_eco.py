from pathlib import Path
from collections import Counter
import odb,json,hashlib
R=Path("/work/routing")
source=R/"runs/routed_final/1-openroad-detailedrouting/drt_iter52.odb"
from openroad import Tech,Design
ort=Tech();design=Design(ort);design.readDb(str(source));d=design.getDb()
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

out=R/'reports/manual_search';out.mkdir(exist_ok=True)
design.evalTclString('set_thread_count 2')
target=b.findNet('_10901_');w=target.getWire();before,ids=primitives(w)
orig=odb.dbWireGraph();orig.decode(w)
cuts=[('met1',(1616670,600610),(1623115,600610)),('met1',(1623115,600610),(1623115,601630)),('met1',(1623115,601630),(1626790,601630))]
def reset():
 orig.encode(w);normalize_routes(w);restore_patches(w,before)
 assert primitives(w)[0]==before
def check(tag):
 path=out/(tag+'.rpt')
 design.evalTclString(f'drt::check_drc -box {{1600000 560000 1640000 615000}} -output_file {path} -marker_name Search')
 text=path.read_text();count=text.count('violation type:')
 print('SEARCH',tag,count,flush=True)
 return count
assert check('baseline')==2
via=choose_via('met1','met2')
audit=[]
for x in [1623115,1623570,1622650,1622190,1624030]:
 reset();p,ids=primitives(w);g=odb.dbWireGraph();g.decode(w)
 for k in cuts:g.deleteEdge(g.getEdge(ids[k]))
 pts=[(1616670,600610,'met1'),(x,600610,'met1'),(x,600610,'met2'),(x,601630,'met2'),(x,601630,'met1'),(1626790,601630,'met1')]
 nodes=[g.createNode(a,z,tech.findLayer(l)) for a,z,l in pts]
 for i in range(len(nodes)-1):
  if pts[i][2]==pts[i+1][2]:g.createSegment(nodes[i],nodes[i+1])
  else:g.createTechVia(nodes[i],nodes[i+1],via)
 g.encode(w);normalize_routes(w);restore_patches(w,before)
 n=check('first_'+str(x));audit.append([x,n])
 if n==1:
  odb.write_db(d,str(R/'inputs/route_first_manual.odb'));print('FIRST_CANDIDATE',x,flush=True);break
(out/'first_search.json').write_text(json.dumps(audit,indent=2))
