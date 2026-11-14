from pathlib import Path
from collections import defaultdict
import hashlib,json,pya
C=Path('/work/week25_closure');data=json.loads((C/'reports/li1_actual_context.json').read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
source=Path(data['source_GDS']);assert sha(source)==data['source_GDS_sha256']
l=pya.Layout();l.read(str(source));assert l.dbu==.001;top=l.cell('fault_v_asic_top');li_index=l.find_layer(67,20);ce_index=l.find_layer(81,2);assert li_index is not None and ce_index is not None
roi=pya.Region([pya.Box(*r) for r in data['rois_dbu']]).merged()
context=roi.sized(15000).merged();li=pya.Region();ce=pya.Region()
for window in context.each():
    li+=pya.Region(top.begin_shapes_rec_overlapping(li_index,window.bbox()))
    ce+=pya.Region(top.begin_shapes_rec_overlapping(ce_index,window.bbox()))
li.merge();ce.merge()
cross=li.outside(ce)|(li.interacting(ce)-li.inside(ce));local=li.interacting(roi.sized(2000))
owners=defaultdict(pya.Region);routed=set();diagnostics=[]
for poly in local.each():
    r=pya.Region(poly);box=poly.bbox();bounds=[box.left,box.bottom,box.right,box.top]
    hit=lambda q:bounds[0]<=q[2] and bounds[2]>=q[0] and bounds[1]<=q[3] and bounds[3]>=q[1] and not (r&pya.Region(pya.Box(*q))).is_empty()
    wn={n for n,q in data['wire_li1_shapes'] if hit(q)};pn={row[0] for row in data['pin_li1_shapes'] if hit(row[1])}
    names=wn|pn
    if wn:assert len(names)==1,('Actual LI1 component has multiple port/wire owners',names,bounds)
    if len(names)==1:
        name=next(iter(names));owners[name]+=r
        if wn and not (r&cross&roi).is_empty():routed.add(name)
    diagnostics.append({'bbox':bounds,'wire_owners':sorted(wn),'pin_owners':sorted(pn)})
patches=[];proposals={}
for name in sorted(routed):
    r=owners[name].merged();closed=r.sized(100,2).sized(-100,2);difference=(closed-r).interacting(roi)
    rects=pya.Region();rect_boxes=set()
    for poly in difference.decompose_trapezoids_to_region().each():
        q=poly.bbox();assert min(q.width(),q.height())<=250 and max(q.width(),q.height())<=10000 and q.width()*q.height()<=1000000,('Large gap closure refused',name,str(q))
        coords=((q.left//5)*5,(q.bottom//5)*5,((q.right+4)//5)*5,((q.top+4)//5)*5);assert (pya.Region(pya.Box(*coords))-context).is_empty();rect_boxes.add(coords);rects.insert(pya.Box(*coords))
    rects.merge();foreign=local-r
    assert (rects&foreign).is_empty() and rects.interacting(foreign).is_empty(),('Gap closure touches foreign LI1',name)
    assert rects.separation_check(foreign,170).is_empty(),('Gap closure approaches foreign LI1',name)
    for other,prior in proposals.items():
        assert (rects&prior).is_empty() and rects.interacting(prior).is_empty() and rects.separation_check(prior,170).is_empty(),('Different-net patches approach',name,other)
    proposals[name]=rects
    for coords in sorted(rect_boxes):
        box=list(coords);patches.append({'net':name,'layer':'li1','box_dbu':box});top.shapes(li_index).insert(pya.Box(*coords))
assert patches
target=C/'inputs/li1_spacing_simulated.gds';assert not target.exists();l.write(str(target))
out=C/'reports/li1_closure_plan.json';assert not out.exists();out.write_text(json.dumps({'source_GDS_sha256':sha(source),'simulated_GDS':str(target),'simulated_GDS_sha256':sha(target),'source_rule_markers':43,'whole_polygon_context_radius_dbu':15000,'patches':patches,'component_ownership':diagnostics,'scope':'Actual GDS same-owner LI1 component notch closure near the 43 rule markers. No foreign conductor overlap or 0.17um approach allowed; full rule replay and actual core LVS still required.'},indent=2)+'\n')
print('ACTUAL_LI1_CLOSURE_PLANNED',len(patches),sorted(routed),flush=True)
