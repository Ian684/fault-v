from pathlib import Path
from collections import defaultdict
import hashlib,json,pya
C=Path('/work/week25_closure');data=json.loads((C/'reports/m_li1_actual_context.json').read_text())
edge_proof=json.loads((C/'reports/m_li1_edge_ownership.json').read_text());assert edge_proof['same_component_notches']==23 and edge_proof['different_component_spacing']==0
bad_components=set()
for edge in edge_proof['edge_pairs']:
    for side in edge['owners']:
        assert len(side)==1 and len(side[0]['wire_owners'])==1
        info=side[0];bad_components.add((info['wire_owners'][0],tuple(info['bbox_dbu'])))
assert len(bad_components)==5
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
        name=next(iter(names))
        if (name,tuple(bounds)) in bad_components:owners[name]+=r;routed.add(name)
    diagnostics.append({'bbox':bounds,'wire_owners':sorted(wn),'pin_owners':sorted(pn)})
patches=[];proposals={}
for name in sorted(routed):
    r=owners[name].merged();closed=r.sized(100,2).sized(-100,2);difference=(closed-r).interacting(roi)
    rects=pya.Region();rect_boxes=set()
    for poly in difference.decompose_trapezoids_to_region().each():
        q=poly.bbox();assert min(q.width(),q.height())<=250 and max(q.width(),q.height())<=10000 and q.width()*q.height()<=1000000,('Large gap closure refused',name,str(q))
        coords=((q.left//5)*5,(q.bottom//5)*5,((q.right+4)//5)*5,((q.top+4)//5)*5);assert (pya.Region(pya.Box(*coords))-context).is_empty();rect_boxes.add(coords);rects.insert(pya.Box(*coords))
    rects.merge();allowed=(r|rects).merged();expanded=pya.Region();wide_boxes=set()
    for a,c,z,f in sorted(rect_boxes):
        dx=max(0,170-(z-a));dy=max(0,170-(f-c));chosen=None
        offsets_x=sorted(range(0,dx+1,5),key=lambda k:(abs(2*k-dx),k));offsets_y=sorted(range(0,dy+1,5),key=lambda k:(abs(2*k-dy),k))
        for ox in offsets_x:
            for oy in offsets_y:
                q=(a-ox,c-oy,z+dx-ox,f+dy-oy)
                if (pya.Region(pya.Box(*q))-allowed).is_empty():chosen=q;break
            if chosen:break
        assert chosen,('No >=170nm rectangular encoding within exact closed mask',name,(a,c,z,f))
        wide_boxes.add(chosen);expanded.insert(pya.Box(*chosen))
    expanded.merge();assert ((r|expanded)^allowed).is_empty()
    rects=expanded;rect_boxes=wide_boxes;foreign=local-r
    assert (rects&foreign).is_empty() and rects.interacting(foreign).is_empty(),('Gap closure touches foreign LI1',name)
    assert rects.separation_check(foreign,170).is_empty(),('Gap closure approaches foreign LI1',name)
    for other,prior in proposals.items():
        assert (rects&prior).is_empty() and rects.interacting(prior).is_empty() and rects.separation_check(prior,170).is_empty(),('Different-net patches approach',name,other)
    proposals[name]=rects
    for coords in sorted(rect_boxes):
        box=list(coords);patches.append({'net':name,'layer':'li1','box_dbu':box});top.shapes(li_index).insert(pya.Box(*coords))
assert patches
target=C/'inputs/m_li1_closed_wide.gds';assert not target.exists();l.write(str(target))
out=C/'reports/m_li1_closure_wide_plan.json';assert not out.exists();out.write_text(json.dumps({'source_GDS_sha256':sha(source),'simulated_GDS':str(target),'simulated_GDS_sha256':sha(target),'source_rule_markers':23,'minimum_rectangle_dimension_dbu':170,'all_23_violations_measured_as_same_component_notches':True,'whole_polygon_context_radius_dbu':15000,'patches':patches,'component_ownership':diagnostics,'scope':'Actual GDS same-owner LI1 component notch closure only on the five actually violating new-wire components near 23 rule markers. No foreign conductor overlap or 0.17um approach allowed; full rule replay and actual core LVS still required.'},indent=2)+'\n')
print('ACTUAL_LI1_CLOSURE_PLANNED',len(patches),sorted(routed),flush=True)
