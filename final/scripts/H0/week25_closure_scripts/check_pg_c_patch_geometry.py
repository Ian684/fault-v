from pathlib import Path
import json,sys,pya
C=Path('/work/week25_closure');planfile=C/(sys.argv[1] if len(sys.argv)>1 else 'reports/pg_c_plan.json');plan=json.loads(planfile.read_text())
l=pya.Layout();l.read('/runtime/fault_v_asic_top.gds');t=l.cell('fault_v_asic_top');u=l.dbu
assert u==.001
idx=l.find_layer(71,20);assert idx is not None
rows=[]
for row in plan['wire_patches']:
    patch=pya.Region(pya.Box(*row['box']));box=patch.bbox().enlarged(2000)
    original=pya.Region(t.begin_shapes_rec_overlapping(idx,box))&pya.Region(box);original.merge()
    x1,y1,x2,y2=row['box'];x=(x1+x2)//2
    centerline=pya.Region(pya.Box(x-100,y1,x+100,y2))
    intended=original.interacting(centerline);other=original-intended
    missing=(centerline-original).area();short=(patch&other).area();spacing=patch.separation_check(other,300).size()
    assert not intended.is_empty()
    rows.append({**row,'centerline_outside_existing_M4_dbu2':missing,'overlap_other_M4_dbu2':short,'space_to_other_M4_below_0p3um':spacing})
    print('PG_C_M4_SCREEN',row['net'],row['box'],missing,short,spacing,flush=True)
passed=all(r['centerline_outside_existing_M4_dbu2']==r['overlap_other_M4_dbu2']==r['space_to_other_M4_below_0p3um']==0 for r in rows)
plan.update(geometry_screen_pass=passed,geometry_screens=rows)
planfile.write_text(json.dumps(plan,indent=2)+'\n');assert passed
