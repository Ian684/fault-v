from pathlib import Path
from collections import defaultdict
import hashlib,json,pya
C=Path('/work/week25_closure');data=json.loads((C/'reports/m_li1_actual_context.json').read_text());source=Path(data['source_GDS'])
with source.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==data['source_GDS_sha256']
l=pya.Layout();l.read(str(source));assert l.dbu==.001;top=l.cell('fault_v_asic_top');li_index=l.find_layer(67,20);ce_index=l.find_layer(81,2)
roi=pya.Region([pya.Box(*r) for r in data['rois_dbu']]).merged();context=roi.sized(15000).merged();li=pya.Region();ce=pya.Region()
for window in context.each():
    li+=pya.Region(top.begin_shapes_rec_overlapping(li_index,window.bbox()));ce+=pya.Region(top.begin_shapes_rec_overlapping(ce_index,window.bbox()))
li.merge();ce.merge();cross=li.outside(ce)|(li.interacting(ce)-li.inside(ce));local=li.interacting(roi.sized(2000));rows=[]
for poly in local.each():
    r=pya.Region(poly);box=poly.bbox();bounds=[box.left,box.bottom,box.right,box.top]
    hit=lambda q:bounds[0]<=q[2] and bounds[2]>=q[0] and bounds[1]<=q[3] and bounds[3]>=q[1] and not (r&pya.Region(pya.Box(*q))).is_empty()
    wn=sorted({n for n,q in data['wire_li1_shapes'] if hit(q)});pins=[row for row in data['pin_li1_shapes'] if hit(row[1])]
    near_rule=not (r&cross&roi).is_empty()
    if wn or near_rule:rows.append({'bbox_dbu':bounds,'wire_owners':wn,'pin_names':sorted({p[2]+'/'+p[3] for p in pins}),'pin_net_owners':sorted({p[0] for p in pins}),'crosses_CE_near_violation':near_rule,'outside_CE_area_um2':(r-ce).area()*l.dbu*l.dbu})
masters={}
for name in ('sky130_fd_sc_hd__diode_2','sky130_fd_sc_hd__buf_1','sky130_fd_sc_hd__clkbuf_2'):
    cell=l.cell(name)
    if cell:
        masters[name]={}
        for layer,dt in ((67,20),(81,2)):
            index=l.find_layer(layer,dt);r=pya.Region(cell.begin_shapes_rec(index));masters[name][f'{layer}/{dt}']={'bbox':str(r.bbox()),'polygons':r.size(),'area_um2':r.area()*l.dbu*l.dbu}
out=C/'reports/m_li1_components.json';assert not out.exists();out.write_text(json.dumps({'source_GDS_sha256':data['source_GDS_sha256'],'components':rows,'master_shapes':masters,'scope':'Read-only actual-GDS ownership/CE diagnostic; no technology rule or geometry changed.'},indent=2)+'\n')
print('M_LI1_COMPONENTS',json.dumps(rows),flush=True);print('MASTER_LI1_CE',json.dumps(masters),flush=True)
