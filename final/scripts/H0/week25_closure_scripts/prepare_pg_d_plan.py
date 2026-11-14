"""Cover the remaining redistributed EM hotspot and measured 90%-utilization branches."""
from pathlib import Path
import ast,copy,json
C=Path(__file__).resolve().parents[1]
prior=json.loads((C/'reports/pg_c_applied.json').read_text())
base=json.loads((C/'reports/pg_via_plan_b.json').read_text())
audit=json.loads((C/'reports/pg_c_em_resistor_audit.json').read_text())
assert len(audit['violations'])==1
changes={(r['net'],*r['before']['old_xy']):r for r in prior['via_changes']};patches=copy.deepcopy(prior['wire_patches'])
tree=ast.parse((C/'scripts/prepare_pg_c_plan.py').read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='select_array')
exec(compile(ast.Module(body=[function],type_ignores=[]),'select_array','exec'))
for net,case in audit['cases']['0p028'].items():
    for row in case['near_limit_branches_over_90_percent']:
        a,b=row['node0'],row['node1']
        if row['layer']=='met4':
            assert a[1]==b[1];x=a[1]
            candidates=[r for r in base['planned_replacements'] if r['net']==net and r['old_xy'][0]==x]
            r=min(candidates,key=lambda r:abs(r['old_xy'][1]-(a[2]+b[2])/2))
            assert min(abs(r['old_xy'][1]-a[2]),abs(r['old_xy'][1]-b[2]))<50000
            r=select_array(r)
            patches.append({'net':net,'box':[x-1400,min(a[2],b[2],r['new_bottom_box'][1])-1400,x+1400,max(a[2],b[2],r['new_bottom_box'][3])+1400],'reason':'Redistributed M4 branch above 90% current utilization; continuous width through feed array'})
        else:
            assert row['layer']=='via4'
            lower=a if a[0]=='met4' else b
            hits=[r for r in base['planned_replacements'] if r['net']==net and r['new_bbox'][0]<=lower[1]<=r['new_bbox'][2] and r['new_bbox'][1]<=lower[2]<=r['new_bbox'][3]]
            assert len(hits)==1
            select_array(hits[0])
record={'source_ODB_sha256':base['output_sha256'],'wire_patches':patches,'via_changes':list(changes.values()),'geometry_screen_pass':False,'accepted':False,'scope':prior['scope'],'prior_current_audit':'reports/pg_c_em_resistor_audit.json','prior_actual_stress_violations':1,'additional_margin_screen_threshold':.9}
(C/'reports/pg_d_plan.json').write_text(json.dumps(record,indent=2)+'\n')
print('PG_D_PLAN',len(patches),'M4 patches',len(changes),'compact arrays, including prior C repairs')
wrapper=(C/'scripts/run_pg_c.sh').read_text().replace('pg_c','pg_d').replace('pg-c','pg-d').replace('pg_stream_c','pg_stream_d')
(C/'scripts/run_pg_d.sh').write_text(wrapper,newline='\n')
