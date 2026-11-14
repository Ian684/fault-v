from pathlib import Path
import hashlib,json,re,sys,xml.etree.ElementTree as ET
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
C=Path('/work/week25_closure');run=C/'runs/focus_post_a'
source=run/'1-openroad-fillinsertion/fault_v_asic_top.odb';gds=run/'2-klayout-streamout/fault_v_asic_top.gds'
root=ET.parse(run/'3-klayout-drc/reports/drc.klayout.lyrdb').getroot();rois=[]
items=root.findall('items/item');assert len(items)==43 and all(i.findtext('category').strip("'")=='li.3' for i in items)
for item in items:
    for v in item.findall('values/value'):
        nums=[round(float(x)*1000) for x in re.findall(r'-?\d+(?:\.\d+)?',v.text or '')];assert len(nums)==8
        rois.append([min(nums[::2])-500,min(nums[1::2])-500,max(nums[::2])+500,max(nums[1::2])+500])
near=lambda q:any(q[0]<=r[2]+2000 and q[2]>=r[0]-2000 and q[1]<=r[3]+2000 and q[3]>=r[1]-2000 for r in rois)
db,b=load(source);tech=db.getTech();wires=[];pins=[]
for n in b.getNets():
    if not n.getWire():continue
    for q in primitives(n.getWire())[0]:
        boxes=[]
        if q[0]=='S' and q[1]=='li1':
            _,l,x1,y1,x2,y2,e1,e2=q;h=85;boxes=[[x1-h,y1-e1,x2+h,y2+e2] if x1==x2 else [x1-e1,y1-h,x2+e2,y2+h]]
        elif q[0]=='R' and q[1]=='li1':boxes=[list(q[2:6])]
        elif q[0] in ('T','V'):
            v=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);x,y=q[2:4]
            boxes=[[z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y] for z in v.getBoxes() if z.getTechLayer().getName()=='li1']
        for box in boxes:
            if near(box):wires.append([n.getName(),box])
for i in b.getInsts():
    z=i.getBBox()
    if not near([z.xMin(),z.yMin(),z.xMax(),z.yMax()]):continue
    for p in i.getITerms():
        if not p.getNet():continue
        for l,z in p.getGeometries():
            box=[z.xMin(),z.yMin(),z.xMax(),z.yMax()]
            if l.getName()=='li1' and near(box):pins.append([p.getNet().getName(),box,i.getName(),p.getMTerm().getName()])
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
out=C/'reports/li1_actual_context.json';assert not out.exists();out.write_text(json.dumps({'source_filled_ODB_sha256':sha(source),'source_GDS':str(gds),'source_GDS_sha256':sha(gds),'rule':'li.3','markers':43,'rois_dbu':rois,'wire_li1_shapes':wires,'pin_li1_shapes':pins},indent=2)+'\n')
print('LI1_GDS_CONTEXT_EXPORTED',len(wires),len(pins),flush=True)
