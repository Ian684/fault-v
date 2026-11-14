from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/plan_actual_li1_closure.py').read_text()
start=code.index("li=pya.Region(top.begin_shapes_rec(li_index))")
end=code.index('cross=li.outside',start)
code=code[:start]+'''roi=pya.Region([pya.Box(*r) for r in data['rois_dbu']]).merged()
context=roi.sized(15000).merged();li=pya.Region();ce=pya.Region()
for window in context.each():
    li+=pya.Region(top.begin_shapes_rec_overlapping(li_index,window.bbox()))
    ce+=pya.Region(top.begin_shapes_rec_overlapping(ce_index,window.bbox()))
li.merge();ce.merge()
'''+code[end:]
code=code.replace("q=poly.bbox();assert q.width()<=2000 and q.height()<=2000,('Large gap closure refused',name,str(q))","q=poly.bbox();assert min(q.width(),q.height())<=250 and max(q.width(),q.height())<=10000 and q.width()*q.height()<=1000000,('Large gap closure refused',name,str(q))")
code=code.replace("rect_boxes.add(coords);rects.insert(pya.Box(*coords))","assert (pya.Region(pya.Box(*coords))-context).is_empty();rect_boxes.add(coords);rects.insert(pya.Box(*coords))")
code=code.replace("'source_rule_markers':43","'source_rule_markers':43,'whole_polygon_context_radius_dbu':15000")
code=code.replace('for poly in difference.each():','for poly in difference.decompose_trapezoids_to_region().each():')
p=C/'scripts/plan_actual_li1_closure_local.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('WHOLE_POLYGON_LOCAL_LI1_PLAN_PREPARED')
