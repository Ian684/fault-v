"""Check complete FOM dummy islands against public local geometric requirements."""
from pathlib import Path
import hashlib,json,sys,pya
basefile,fillfile,report=map(Path,sys.argv[1:4])
base=pya.Layout();fill=pya.Layout();base.read(str(basefile));fill.read(str(fillfile))
assert base.dbu==fill.dbu;u=base.dbu;bt=base.cell('fault_v_asic_top');ft=fill.top_cell();assert bt and ft
def region(layout,cell,spec,box=None):
    r=pya.Region()
    for a,z in spec:
        idx=layout.find_layer(a,z)
        if idx is not None:r+=pya.Region(cell.begin_shapes_rec(idx) if box is None else cell.begin_shapes_rec_overlapping(idx,box))
    if box is not None:r&=pya.Region(box)
    r.merge();return r
fom=region(fill,ft,[(65,99),(23,28)]);assert not fom.is_empty()
checks={'minimum_width':fom.width_check(round(.5/u)).size(),'minimum_spacing':fom.space_check(round(.4/u)).size()}
checks['over_maximum_dimension']=sum(max(p.bbox().width(),p.bbox().height())*u>25 for p in fom.each())
assert pya.Region(pya.Box(0,0,100,100)).width_check(500).size()>0
tiles=[]
for y in range(0,3300,700):
    for x in range(0,2500,700):
        roi=pya.Box(round(x/u),round(y/u),round(min(x+700,2500)/u),round(min(y+700,3300)/u))
        local=fom.interacting(pya.Region(roi));assert not local.is_empty()
        box=local.bbox().enlarged(round(1/u))
        get=lambda spec:region(base,bt,spec,box)
        nw=get([(64,20)]);ns=get([(93,44)]);ps=get([(94,20)])
        inside=local.inside(nw);outside=local.outside(nw)
        values={'diff_overlap':(local&get([(65,20),(65,44)])).area(),'poly_overlap':(local&get([(66,20)])).area(),'nsdm_spacing':local.separation_check(ns,round(.13/u)).size(),'psdm_spacing':local.separation_check(ps,round(.13/u)).size(),'nwell_crossing':(local-(inside|outside)).area(),'nwell_enclosure':(inside-nw.sized(-round(.18/u))).area(),'nwell_outside_spacing':(outside&nw.sized(round(.34/u))).area(),'THKOX_source_area':get([(75,20)]).area(),'VHVI_source_area':get([(74,21)]).area()}
        tiles.append({'x_um':x,'y_um':y,'checks':values});print('FULL_FOM_TILE',x,y,values,flush=True)
passed=all(v==0 for v in checks.values()) and all(v==0 for t in tiles for v in t['checks'].values())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
record={'source_sha256':sha(basefile),'fill_sha256':sha(fillfile),'global_checks':checks,'tiles':tiles,'negative_control_detected':True,'screen_pass':passed,'scope':'Whole FOM dummy islands, globally checked width/spacing/max dimension and local actual diffusion/poly/implant/nwell interactions. Overlapping tiles retain entire islands to avoid artificial clipping. Public open-PDK screen; seal/frame and foundry qualification remain outside coverage.'}
report.write_text(json.dumps(record,indent=2)+'\n');assert passed,'Full FOM geometry failed; see report'
print('FULL_FOM_PASS',len(tiles),flush=True)
