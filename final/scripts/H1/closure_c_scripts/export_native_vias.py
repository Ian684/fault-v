"""Inventory every actual regular/special route via and its native geometry."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,primitives
source,report=map(Path,sys.argv[1:3]);db,b=load(source);counts=Counter();objects={}
for net in b.getNets():
    if net.getWire():
        for q,count in primitives(net.getWire())[0].items():
            if q[0] in ('T','V'):
                counts[q[1]]+=count;v=db.getTech().findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);assert v;objects[q[1]]=v
    for sw in net.getSWires():
        for q in sw.getWires():
            if q.isVia():v=q.getTechVia() or q.getBlockVia();assert v;counts[v.getName()]+=1;objects[v.getName()]=v
assert sum(counts.values())>400000 and set(counts)==set(objects)
vias={n:{'instances':counts[n],'boxes':[(q.getTechLayer().getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax()) for q in objects[n].getBoxes()]} for n in counts}
with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
report.write_text(json.dumps({'source_ODB_sha256':digest,'db_units_per_um':b.getDbUnitsPerMicron(),'component_master_counts':dict(Counter(i.getMaster().getName() for i in b.getInsts())),'vias':vias,'all_actual_regular_and_special_wire_vias_inventoried':True},indent=2)+'\n')
print('NATIVE_VIA_INVENTORY',len(vias),sum(counts.values()),digest,flush=True)
