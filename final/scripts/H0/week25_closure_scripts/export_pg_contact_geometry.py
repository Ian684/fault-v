"""Export physical PG copper, including generated-via enclosures and actual SRAM PG pins."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load
source,report=map(Path,sys.argv[1:3]);db,b=load(source);metal={'li1','met1','met2','met3','met4','met5'};shapes={n:[] for n in ('VPWR','VGND')}
def add(net,layer,box,owner):
    if layer in metal:shapes[net].append([layer,*box,owner])
for name in shapes:
    net=b.findNet(name);assert net and net.getWire() is None
    for sidx,sw in enumerate(net.getSWires()):
        for idx,q in enumerate(sw.getWires()):
            if not q.isVia():add(name,q.getTechLayer().getName(),(q.xMin(),q.yMin(),q.xMax(),q.yMax()),f'sbox:{sidx}:{idx}:stripe')
            else:
                v=q.getTechVia() or q.getBlockVia();x,y=q.getViaXY()
                for z in v.getBoxes():add(name,z.getTechLayer().getName(),(x+z.xMin(),y+z.yMin(),x+z.xMax(),y+z.yMax()),f'sbox:{sidx}:{idx}:via:{v.getName()}:{x}:{y}')
    for p in net.getITerms():
        if not p.getInst().getMaster().isBlock():continue
        for l,z in p.getGeometries():add(name,l.getName(),(z.xMin(),z.yMin(),z.xMax(),z.yMax()),'SRAM:'+p.getInst().getName()+'/'+p.getMTerm().getName())
    for term in net.getBTerms():
        for pin in term.getBPins():
            for z in pin.getBoxes():add(name,z.getTechLayer().getName(),(z.xMin(),z.yMin(),z.xMax(),z.yMax()),'BTerm:'+term.getName())
with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
assert report.parent.exists() and not report.exists();report.write_text(json.dumps({'source_sha256':digest,'source':str(source),'dbu_per_um':b.getDbUnitsPerMicron(),'shapes':shapes,'scope':'All native PG special-wire and via-enclosure copper plus SRAM PG pins and top PG ports. Standard-cell master PG pins are unchanged and only occupy lower layers; full actual core LVS is still mandatory.'})+'\n')
print('PG_CONTACT_GEOMETRY',digest,{n:len(v) for n,v in shapes.items()},flush=True)
