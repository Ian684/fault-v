"""Reuse exact existing via geometry instead of emitting a coincident duplicate."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs.py').read_text().replace('antenna_stubs_a','antenna_stubs_c')
b=(C/'scripts/append_antenna_stubs_b.py').read_text()
start=b.index('prior=json.loads(');end=b.index('for row,roi in zip(targets,regions):',start)
resume=b[start:end]
code=code.replace('accepted=[];paths=defaultdict(list)','accepted=[];paths=defaultdict(list)\n'+resume)
code=code.replace('for row,roi in zip(targets,regions):',"for row,roi in zip(targets,regions):\n    if row['diode'] in resumed:continue")
marker="    e=odb.dbWireEncoder();e.append(net.getWire());added=Counter()"
assert code.count(marker)==1
code=code.replace(marker,'''    existing=defaultdict(list)
    boxes=lambda v:Counter((q.getTechLayer().getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax()) for q in v.getBoxes())
    for q in primitives(net.getWire())[0]:
        if q[0] in ('T','V'):
            via=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1])
            existing[q[2],q[3]].append(boxes(via))
'''+marker)
marker="            e.newPath(v.getBottomLayer(),'ROUTED');e.addPoint(*a[:2]);e.addTechVia(v)"
assert code.count(marker)==1
code=code.replace(marker,"            if boxes(v) in existing[tuple(a[:2])]:\n                print('EXACT_EXISTING_VIA_REUSED',net.getName(),v.getName(),a[:2],flush=True);continue\n"+marker)
p=C/'scripts/append_antenna_stubs_c.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('EXACT_VIA_REUSE_STUB_C_PREPARED')
