"""Plan local M4 widening and compact eight-cut arrays for measured EM hotspots."""
from pathlib import Path
import copy,json
C=Path(__file__).resolve().parents[1]
plan=json.loads((C/'reports/pg_via_plan_b.json').read_text())
audit=json.loads((C/'reports/pg_em_resistor_audit.json').read_text());assert len(audit['violations'])==16
changes={};patches=[]
def select_array(r):
    key=(r['net'],*r['old_xy'])
    if key in changes:return changes[key]['after']
    assert (r['cols'],r['rows'])==(1,8)
    prior=copy.deepcopy(r);r=copy.deepcopy(r);x,old_y=r['old_xy']
    y=r['old_bbox'][3]-3110 if r['new_xy'][1]<old_y else r['old_bbox'][1]+3110
    r.update(cols=2,rows=4,XBottomEnclosure=190,YBottomEnclosure=190,XTopEnclosure=310,YTopEnclosure=310,new_xy=[x,y],new_bottom_box=[x-1390,y-2990,x+1390,y+2990],new_top_box=[x-1510,y-3110,x+1510,y+3110],new_cut_count=8,new_via='W25_PG_VIA4_2_4_190_190_310_310')
    r['new_bbox']=r['new_top_box']
    changes[key]={'net':r['net'],'before':prior,'after':copy.deepcopy(r)}
    patches.append({'net':r['net'],'box':[x-1400,y-3190,x+1400,y+3190],'reason':'Support compact 2x4 via4 array on widened existing PG rail'})
    return r
for row in audit['violations']:
    net=row['net'];a,b=row['node0'],row['node1']
    if row['layer']=='met4':
        assert a[1]==b[1];x=a[1]
        candidates=[r for r in plan['planned_replacements'] if r['net']==net and r['old_xy'][0]==x]
        r=min(candidates,key=lambda r:abs(r['old_xy'][1]-(a[2]+b[2])/2))
        assert min(abs(r['old_xy'][1]-a[2]),abs(r['old_xy'][1]-b[2]))<50000
        r=select_array(r)
        patches.append({'net':net,'box':[x-1400,min(a[2],b[2],r['new_bottom_box'][1])-1400,x+1400,max(a[2],b[2],r['new_bottom_box'][3])+1400],'reason':'Measured M4 average-current violation; widened continuously through its feeding array','source_nodes':[a,b]})
    else:
        assert row['layer']=='via4'
        lower=a if a[0]=='met4' else b
        hits=[r for r in plan['planned_replacements'] if r['net']==net and r['new_bbox'][0]<=lower[1]<=r['new_bbox'][2] and r['new_bbox'][1]<=lower[2]<=r['new_bbox'][3]]
        assert len(hits)==1,(row,hits)
        select_array(hits[0])
assert changes and patches
record={'source_ODB_sha256':plan['output_sha256'],'wire_patches':patches,'via_changes':list(changes.values()),'geometry_screen_pass':False,'accepted':False,'scope':'Only measured stress-load hotspots. M4 width 2.8um (existing 1.74um rails) and real 2x4 via4 arrays. Actual full-macro manufacturing geometry, opposite supply clearance, native current redistribution, and final full DRC must be checked.'}
(C/'reports/pg_c_plan.json').write_text(json.dumps(record,indent=2)+'\n')
print('PG_C_PLAN',len(patches),'M4 patches',len(changes),'compact arrays')
