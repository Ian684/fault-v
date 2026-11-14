"""Compare every actually used cell and component count with the fresh DEF/library."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sys,pya
gds,def_file,report,native_via_report=map(Path,sys.argv[1:5])
C=Path('/work/week25_closure');library=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds'
text=def_file.read_text();match=re.search(r'(?ms)^COMPONENTS\s+(\d+)\s*;(.*?)^END COMPONENTS',text);assert match
masters=Counter(re.findall(r'(?m)^\s*-\s+\S+\s+(\S+)',match[2]));assert sum(masters.values())==int(match[1])
assert masters['sky130_sram_2kbyte_1rw1r_32x512_8']==18
source=pya.Layout();target=pya.Layout();source.read(str(library));target.read(str(gds));top=target.cell('fault_v_asic_top');assert top
actual=Counter(target.cell(i.cell_index).name for i in top.each_inst())
native=json.loads(native_via_report.read_text());assert Counter(native['component_master_counts'])==masters
via_counts=Counter({'VIA_'+n:r['instances'] for n,r in native['vias'].items()})
assert actual==masters+via_counts,(actual-masters-via_counts,masters+via_counts-actual)
assert source.dbu==target.dbu
specs={(i.layer,i.datatype) for i in source.layer_infos()}|{(i.layer,i.datatype) for i in target.layer_infos()};results={}
for name,count in masters.items():
    if not name.startswith('sky130_fd_sc_hd__'):continue
    a=source.cell(name);b=target.cell(name);assert a and b,name
    nonempty=False;checks={}
    for spec in sorted(specs):
        ai=source.find_layer(*spec);bi=target.find_layer(*spec)
        ref=pya.Region(a.begin_shapes_rec(ai)) if ai is not None else pya.Region()
        value=pya.Region(b.begin_shapes_rec(bi)) if bi is not None else pya.Region()
        nonempty|=not ref.is_empty();same=(ref^value).is_empty();assert same,(name,spec)
        if not ref.is_empty():checks[f'{spec[0]}/{spec[1]}']=True
    assert nonempty,name
    results[name]={'instances':count,'all_polygon_layers_XOR_equal':checks}
control=pya.Region(pya.Box(0,0,100,100));assert not (control^pya.Region(pya.Box(1,0,101,100))).is_empty()
mapping={'li1':(67,20),'mcon':(67,44),'met1':(68,20),'via':(68,44),'met2':(69,20),'via2':(69,44),'met3':(70,20),'via3':(70,44),'met4':(71,20),'via4':(71,44),'met5':(72,20)}
scale=1/(native['db_units_per_um']*target.dbu);assert abs(scale-1)<1e-12
via_checks={}
for name,row in native['vias'].items():
    cell=target.cell('VIA_'+name);assert cell and not any(cell.each_inst())
    expected={}
    for layer,x1,y1,x2,y2 in row['boxes']:
        spec=mapping[layer];expected.setdefault(spec,pya.Region());expected[spec].insert(pya.Box(x1,y1,x2,y2))
    for spec in specs|set(expected):
        li=target.find_layer(*spec);observed=pya.Region(cell.shapes(li)) if li is not None else pya.Region()
        assert (observed^expected.get(spec,pya.Region())).is_empty(),('Route via geometry differs from native ODB',name,spec)
    via_checks[name]={'instances':row['instances'],'all_via_polygon_layers_XOR_equal_native':True}
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
record={'stream_GDS_sha256':sha(gds),'fresh_DEF_sha256':sha(def_file),'native_via_report_sha256':sha(native_via_report),'library_GDS_sha256':sha(library),'all_component_counts_match_fresh_DEF':True,'total_components':sum(masters.values()),'SRAM_instances':18,'standard_cell_instances':sum(v['instances'] for v in results.values()),'used_standard_cell_masters':len(results),'all_used_standard_cell_polygon_layers_match_library':True,'routing_via_instances':sum(via_counts.values()),'all_route_via_counts_and_geometry_match_native_ODB':True,'shifted_polygon_negative_control_detected':True,'masters':results,'route_vias':via_checks,'scope':'Actual DEF/GDS component counts, all polygon-purpose layers of every used standard-cell master, and every regular/special route via count and polygon against native ODB geometry. Text labels and foundry qualification are not inferred; SRAM checked separately.'}
report.write_text(json.dumps(record,indent=2)+'\n');print('FINAL_STDCELL_STREAM_OK',len(results),record['standard_cell_instances'],flush=True)
