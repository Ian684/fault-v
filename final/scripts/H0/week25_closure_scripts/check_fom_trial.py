from pathlib import Path
import json,os,pya
C=Path('/work/week25_closure')
assert (C/'logs/dense_fom_trial.exit').read_text().strip()=='0','Native generation is not complete'
base=pya.Layout();old=pya.Layout();new=pya.Layout()
base.read(str(C/'runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds'))
old.read(str(C/'full_fill_development/fault_v_asic_top_fill_pattern_0_0.gds'))
new.read(os.environ.get('FOM_TRIAL_GDS',str(C/'dense_fom_trial/fault_v_asic_top_fill_pattern_0_0.gds')))
assert base.dbu==old.dbu==new.dbu
u=base.dbu;roi=pya.Box(0,0,round(700/u),round(700/u));bt=base.cell('fault_v_asic_top')
def region(layout,cell,spec):
    r=pya.Region()
    for layer,dt in spec:
        index=layout.find_layer(layer,dt)
        if index is not None:r+=pya.Region(cell.begin_shapes_rec_overlapping(index,roi))
    r&=pya.Region(roi);r.merge();return r
def source(spec):return region(base,bt,spec)
fom=region(new,new.top_cell(),[(65,99)])
actual=source([(65,20),(65,44)]);poly=source([(66,20)])
nw=source([(64,20)]);ns=source([(93,44)]);ps=source([(94,20)])
inside=fom.inside(nw);outside=fom.outside(nw);cross=fom-(inside|outside)
counts={'minimum_width_0p5':fom.width_check(round(.5/u)).size(),'minimum_spacing_0p4':fom.space_check(round(.4/u)).size(),'overlap_actual_diff_um2':(fom&actual).area()*u*u,'overlap_actual_poly_um2':(fom&poly).area()*u*u,'implant_spacing_nsdm_0p13':fom.separation_check(ns,round(.13/u)).size(),'implant_spacing_psdm_0p13':fom.separation_check(ps,round(.13/u)).size(),'crosses_nwell_um2':cross.area()*u*u,'inside_nwell_enclosure_0p18_um2':(inside-nw.sized(-round(.18/u))).area()*u*u,'outside_nwell_spacing_0p34_um2':(outside&nw.sized(round(.34/u))).area()*u*u}
for name,layer in [('THKOX',75),('VHVI',74)]:
    counts[name+'_source_area_um2']=source([(layer,20),(layer,21),(layer,22)]).area()*u*u
metal={}
for layer in range(67,73):
    a=region(old,old.top_cell(),[(layer,99)]);b=region(new,new.top_cell(),[(layer,99)])
    metal[str(layer)]={'XOR_empty':(a^b).is_empty()};assert metal[str(layer)]['XOR_empty']
width_max=max(max(p.bbox().width(),p.bbox().height())*u for p in fom.each())
assert width_max<=25
negative=pya.Region(pya.Box(0,0,100,100))
assert negative.width_check(500).size()>0
record={'scope':'Single 700um tile only. Public FOM dummy width/spacing/implant/well screens and unchanged six metal-fill layers. Die/seal/frame and complete foundry dummy qualification are not established.','FOM_density_before':actual.area()/roi.area(),'FOM_density_after':(actual|fom).area()/roi.area(),'FOM_public_checks':counts,'FOM_maximum_bbox_dimension_um':width_max,'six_metal_layers_unchanged':metal,'negative_width_control_detected':True}
record['screen_pass']=all(v==0 for v in counts.values()) and .33<=record['FOM_density_after']<=.57
Path(os.environ.get('FOM_TRIAL_REPORT',str(C/'reports/dense_fom_trial.json'))).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2),flush=True)
