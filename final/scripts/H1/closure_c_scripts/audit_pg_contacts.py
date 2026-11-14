"""Find physical VPWR/VGND contacts that per-net IR models and geometric DRC cannot identify."""
from pathlib import Path
import hashlib,json,sys,pya
source,report=map(Path,sys.argv[1:3]);data=json.loads(source.read_text());u=data['dbu_per_um'];assert u==1000
assert (pya.Region(pya.Box(0,0,100,100))&pya.Region(pya.Box(50,50,150,150))).area()==2500
assert pya.Region(pya.Box(0,0,100,100)).interacting(pya.Region(pya.Box(101,0,201,100))).is_empty()
assert not pya.Region(pya.Box(0,0,100,100)).interacting(pya.Region(pya.Box(100,0,200,100))).is_empty()
layers={q[0] for rows in data['shapes'].values() for q in rows};results={};contacts=[]
for layer in sorted(layers):
    rows={n:[q for q in values if q[0]==layer] for n,values in data['shapes'].items()};regions={n:pya.Region([pya.Box(*q[1:5]) for q in values]).merged() for n,values in rows.items()}
    overlap=regions['VPWR']&regions['VGND'];touch=regions['VPWR'].interacting(regions['VGND'])
    local=[]
    for poly in overlap.each():
        box=poly.bbox();owners={}
        for name,values in rows.items():owners[name]=[q[5] for q in values if (pya.Region(pya.Box(*q[1:5]))&pya.Region(poly)).area()>0]
        local.append({'layer':layer,'bbox_dbu':[box.left,box.bottom,box.right,box.top],'area_um2':poly.area()/u**2,'owners':owners})
    results[layer]={'overlap_area_um2':overlap.area()/u**2,'overlap_components':len(local),'touching_VPWR_components':touch.count()};contacts+=local
result={'source_geometry_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_ODB_sha256':data['source_sha256'],'layers':results,'positive_area_PG_contacts':contacts,'no_VPWR_VGND_copper_contact':all(v['touching_VPWR_components']==0 for v in results.values()),'scope':data['scope']+' Both overlaps and zero-area edge/point contact are rejected; no technology rule or manufacturing geometry changed.'}
assert not report.exists();report.write_text(json.dumps(result,indent=2)+'\n');print('PG_PHYSICAL_CONTACTS',len(contacts),result['no_VPWR_VGND_copper_contact'],[(k,v) for k,v in results.items() if v['touching_VPWR_components']],flush=True)
