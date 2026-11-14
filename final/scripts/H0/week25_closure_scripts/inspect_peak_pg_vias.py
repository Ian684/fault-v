from pathlib import Path
from collections import Counter
import hashlib,json,shutil,odb
C=Path('/work/week25_closure');W=C.parent/'week25_signoff'
state=json.loads((W/'input_state.json').read_text())
source=Path(state['odb']);temporary=Path('/tmp/faultv-pg-source.odb')
# WSL 9P can stall large sendfile/read requests; use bounded ordinary reads.
with source.open('rb') as inp,temporary.open('wb') as out:shutil.copyfileobj(inp,out,1024*1024)
with source.open('rb') as inp,temporary.open('rb') as out:assert hashlib.file_digest(inp,'sha256').digest()==hashlib.file_digest(out,'sha256').digest()
db=odb.dbDatabase.create();odb.read_db(db,str(temporary))
b=db.getChip().getBlock();u=b.getDbUnitsPerMicron();out={}
for net,x,y in [('VPWR',125.63,866.6),('VPWR',2357.47,866.6),('VGND',122.23,872.6)]:
    xx,yy=round(x*u),round(y*u);found=[]
    for swire in b.findNet(net).getSWires():
        for box in swire.getWires():
            if not box.isVia() or not (box.xMin()<=xx<=box.xMax() and box.yMin()<=yy<=box.yMax()):continue
            via=box.getTechVia() or box.getBlockVia();assert via is not None
            cuts=Counter(q.getTechLayer().getName() for q in via.getBoxes() if str(q.getTechLayer().getType())=='CUT')
            found.append({'name':via.getName(),'bbox_um':[v/u for v in (box.xMin(),box.yMin(),box.xMax(),box.yMax())],'cuts':dict(cuts),'routing_layers':sorted({q.getTechLayer().getName() for q in via.getBoxes() if str(q.getTechLayer().getType())=='ROUTING'})})
    assert found,(net,x,y)
    out[f'{net}:{x},{y}']=found
(C/'reports/peak_PG_via_geometry.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2),flush=True)
