from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/plan_actual_li1_closure_local.py').read_text().replace('reports/li1_actual_context.json','reports/m_li1_actual_context.json')
needle="def sha(p):";assert code.count(needle)==1
prefix="""edge_proof=json.loads((C/'reports/m_li1_edge_ownership.json').read_text());assert edge_proof['same_component_notches']==23 and edge_proof['different_component_spacing']==0
bad_components=set()
for edge in edge_proof['edge_pairs']:
    for side in edge['owners']:
        assert len(side)==1 and len(side[0]['wire_owners'])==1
        info=side[0];bad_components.add((info['wire_owners'][0],tuple(info['bbox_dbu'])))
assert len(bad_components)==5
"""
code=code.replace(needle,prefix+needle)
needle="        name=next(iter(names));owners[name]+=r\n        if wn and not (r&cross&roi).is_empty():routed.add(name)";assert code.count(needle)==1
code=code.replace(needle,"        name=next(iter(names))\n        if (name,tuple(bounds)) in bad_components:owners[name]+=r;routed.add(name)")
needle='    rects.merge();foreign=local-r';assert code.count(needle)==1
replacement="""    rects.merge();allowed=(r|rects).merged();expanded=pya.Region();wide_boxes=set()
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
    rects=expanded;rect_boxes=wide_boxes;foreign=local-r"""
code=code.replace(needle,replacement).replace('inputs/li1_spacing_simulated.gds','inputs/m_li1_closed_wide.gds').replace('reports/li1_closure_plan.json','reports/m_li1_closure_wide_plan.json').replace("'source_rule_markers':43","'source_rule_markers':23,'minimum_rectangle_dimension_dbu':170,'all_23_violations_measured_as_same_component_notches':True").replace('near the 43 rule markers','only on the five actually violating new-wire components near 23 rule markers')
p=C/'scripts/plan_q_li1_closure.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
code=(C/'scripts/apply_actual_li1_closure.py').read_text().replace('/runtime_final/antenna_jumper.odb','/runtime_final/native_group_p.odb').replace('reports/antenna_jumper/result.json','reports/native_group_p/result.json').replace('reports/li1_closure_plan.json','reports/m_li1_closure_wide_plan.json').replace("assert len(plan['patches'])==57","assert plan['source_rule_markers']==23 and plan['minimum_rectangle_dimension_dbu']==170")
code=code.replace("q[0]<q[2] and q[1]<q[3]", "q[2]-q[0]>=170 and q[3]-q[1]>=170")
code=code.replace("out=C/'reports/li1_spacing'", "out=C/'reports/native_group_q'").replace('/runtime_final/li1_spacing.odb','/runtime_final/native_group_q.odb').replace("C/'inputs/li1_spacing.odb'", "C/'inputs/native_group_q.odb'")
needle="groups=defaultdict(list)";assert code.count(needle)==1
code=code.replace(needle,"prior_dr=json.loads((C/'reports/native_group_p_independent.json').read_text());assert prior_dr['odb_sha256']==sha(source) and prior_dr['unresolved_count']==0\n"+needle)
needle="for name,boxes in groups.items():";assert code.count(needle)==1
code=code.replace(needle,"assert set(groups).isdisjoint({'net6033','_10658_','net6330'}), 'The P/M LI1 equivalence guard would not apply'\n"+needle)
code=code.replace("'LI1_rectangles_added':len(plan['patches'])", "'LI1_rectangles_added':len(plan['patches']),'minimum_patch_rectangle_dimension_nm':170")
p=C/'scripts/apply_native_group_q.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('Q_ACTUAL_MASK_SELF_NOTCH_CLOSURE_WITH_170NM_RECTANGLES_PREPARED')
