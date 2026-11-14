from pathlib import Path
import hashlib,json,re,pya
C=Path('/work/week25_closure');folder=C/'fill_tile_trial'
a=pya.Layout();b=pya.Layout();a.read(str(folder/'fault_v_asic_top_fill_pattern.gds.gz'));b.read(str(folder/'canonical_fill.gds.gz'))
assert a.dbu==b.dbu
result={}
for old,new in {65:23,66:28,67:56,68:36,69:41,70:34,71:51,72:59}.items():
    ai=a.find_layer(old,99);bi=b.find_layer(new,28);assert ai is not None and bi is not None
    ar=pya.Region(a.top_cell().begin_shapes_rec(ai));br=pya.Region(b.top_cell().begin_shapes_rec(bi))
    assert (ar^br).is_empty(),old
    result[f'{old}/99 -> {new}/28']={'geometry_XOR_empty':True,'area_um2':ar.area()*a.dbu**2}
assert len(b.layer_infos())==8
tech=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/magic/sky130A-GDS.tech'
text=tech.read_text()
# Both purposes are explicitly mapped to the same internal fill layer by the pinned PDK.
for name,old,new in [('DIFFFILL',65,23),('POLYFILL',66,28),('LI1FILL',67,56),('MET1FILL',68,36),('MET2FILL',69,41),('MET3FILL',70,34),('MET4FILL',71,51),('MET5FILL',72,59)]:
    assert re.search(r'^\s*calma\s+'+name+r'\s+'+str(new)+r'\s+28\s*$',text,re.M),name
    assert re.search(r'^\s*calma\s+ALT'+name+r'\s+'+str(old)+r'\s+99\s*$',text,re.M),name
report={'PDK_tech_sha256':hashlib.sha256(tech.read_bytes()).hexdigest(),'layers':result,'scope':'Documented fill-purpose conversion only. Connected drawing metal (*/20) is never converted or waived.'}
(C/'reports/fill_conversion_sample.json').write_text(json.dumps(report,indent=2)+'\n')
print('ALL_EIGHT_FILL_LAYERS_GEOMETRY_IDENTICAL',flush=True)
