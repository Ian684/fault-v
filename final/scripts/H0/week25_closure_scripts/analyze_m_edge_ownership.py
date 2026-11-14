from pathlib import Path
from collections import defaultdict
import hashlib,json,pya
C=Path('/work/week25_closure');data=json.loads((C/'reports/m_li1_actual_context.json').read_text());source=Path(data['source_GDS'])
with source.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==data['source_GDS_sha256']
l=pya.Layout();l.read(str(source));assert l.dbu==.001;top=l.cell('fault_v_asic_top');li_index=l.find_layer(67,20);ce_index=l.find_layer(81,2)
roi=pya.Region([pya.Box(*r) for r in data['rois_dbu']]).merged();context=roi.sized(15000).merged();li=pya.Region();ce=pya.Region()
for window in context.each():
    li+=pya.Region(top.begin_shapes_rec_overlapping(li_index,window.bbox()));ce+=pya.Region(top.begin_shapes_rec_overlapping(ce_index,window.bbox()))
li.merge();ce.merge();cross=li.outside(ce)|(li.interacting(ce)-li.inside(ce));local=li.interacting(roi.sized(2000));rows=[];components=[]
for poly in local.each():
    r=pya.Region(poly);box=poly.bbox();bounds=[box.left,box.bottom,box.right,box.top]
    hit=lambda q:bounds[0]<=q[2] and bounds[2]>=q[0] and bounds[1]<=q[3] and bounds[3]>=q[1] and not (r&pya.Region(pya.Box(*q))).is_empty()
    wn=sorted({n for n,q in data['wire_li1_shapes'] if hit(q)});pins=[row for row in data['pin_li1_shapes'] if hit(row[1])]
    near_rule=not (r&cross&roi).is_empty()
    info={'bbox_dbu':bounds,'wire_owners':wn,'pin_names':sorted({p[2]+'/'+p[3] for p in pins}),'pin_net_owners':sorted({p[0] for p in pins})};components.append((r,info))
import re,xml.etree.ElementTree as ET
root=ET.parse(C/'runs/native_m_stream_a/3-klayout-drc/reports/drc.klayout.lyrdb').getroot();edges=[]
for item in root.findall('items/item'):
    assert item.findtext('category').strip("'")=='li.3'
    for value in item.findall('values/value'):
        q=[round(float(x)*1000) for x in re.findall(r'-?\d+(?:\.\d+)?',value.text or '')];assert len(q)==8
        owners=[];ids=[]
        for offset in (0,4):
            x=(q[offset]+q[offset+2])//2;y=(q[offset+1]+q[offset+3])//2;point=pya.Region(pya.Box(x-3,y-3,x+3,y+3))
            found=[(i,info) for i,(r,info) in enumerate(components) if not r.interacting(point).is_empty()];ids.append({i for i,info in found});owners.append([info for i,info in found])
        edges.append({'edge_pair_dbu':q,'same_component':bool(ids[0]&ids[1]),'owners':owners})
assert len(edges)==23
record={'source_GDS_sha256':data['source_GDS_sha256'],'same_component_notches':sum(v['same_component'] for v in edges),'different_component_spacing':sum(not v['same_component'] for v in edges),'edge_pairs':edges}
out=C/'reports/m_li1_edge_ownership.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\n')
print('ACTUAL_LI1_EDGE_OWNERSHIP',record['same_component_notches'],record['different_component_spacing'],flush=True)
for e in edges:print(e['same_component'],[[(i['wire_owners'],i['pin_names']) for i in side] for side in e['owners']],e['edge_pair_dbu'],flush=True)
