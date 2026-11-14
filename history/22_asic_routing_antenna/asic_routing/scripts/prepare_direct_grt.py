from pathlib import Path
import json,hashlib,odb
R=Path('/work/routing')
a=json.loads((R/'reports/direct_rc_partial_input.json').read_text())
source=R/a['derived'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)==a['derived_sha256']
d=odb.dbDatabase.create();odb.read_db(d,str(source));b=d.getChip().getBlock()
count=0
for n in b.getNets():
 if n.getSigType() not in ['POWER','GROUND'] and n.getWire() is not None:
  odb.dbWire.destroy(n.getWire());count+=1
assert count==a['retained_wire_count']
out=R/'inputs/direct_rc_grt.odb';assert not out.exists();odb.write_db(d,str(out))
assert sha(source)==a['derived_sha256']
report={'accepted':False,'source':a['derived'],'source_sha256':sha(source),'derived':str(out.relative_to(R)),'derived_sha256':sha(out),'removed_signal_clock_wires':count,'scope':'Separate route-free GRT copy only; original partial-route database remains intact. After GRT, copy verified guides only back to the partial database.'}
(R/'reports/direct_rc_grt_input.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
