from pathlib import Path
from collections import Counter
import json
import re
import odb

w = Path('/work/week25_closure')
report = (w/'runs/probe50_sta_a/1-openroad-staprepnr/max_tt_025C_1v80/checks.rpt').read_text()
slew,cap = report.split('\nmax slew\n',1)[1].split('\nmax capacitance\n',1)
pattern = r'^([^\s]+)\s+([\d.]+)\s+([\d.]+)\s+(-[\d.]+) \(VIOLATED\)'
rows = {kind:[{'pin':m[0],'limit':float(m[1]),'actual':float(m[2]),'slack':float(m[3])} for m in re.findall(pattern,part,re.M)] for kind,part in [('slew',slew),('cap',cap)]}
assert len(rows['slew'])==157 and len(rows['cap'])==17
db=odb.dbDatabase.create()
odb.read_db(db,'/runtime/timing_probe50.odb')
b=db.getChip().getBlock()
for values in rows.values():
    for row in values:
        inst,pin=row['pin'].rsplit('/',1)
        obj=b.findInst(inst)
        assert obj is not None,inst
        it=obj.findITerm(pin)
        assert it is not None and it.getNet(),row['pin']
        net=it.getNet()
        drivers=[p for p in net.getITerms() if str(p.getIoType())=='OUTPUT']
        assert len(drivers)==1,(row['pin'],len(drivers))
        driver=drivers[0]
        row.update(net=net.getName(),driver=driver.getInst().getName()+'/'+driver.getMTerm().getName(),driver_master=driver.getInst().getMaster().getName())
result={'corner':'max_tt_025C_1v80','violations':rows,'affected_nets':len({r['net'] for values in rows.values() for r in values}),
        'driver_masters':dict(Counter({r['driver']:r['driver_master'] for values in rows.values() for r in values}.values())),
        'status':'Real library-limit failures, not waived. No unverified resize applied to the accepted physical candidate.',
        'repair_requirements':'Resize/buffer on a new physical candidate using max RC, check upstream load and hold, legalize, re-route, regenerate all SPEFs and rerun DRC/LVS/antenna/placement/STA; do not reuse old routed parasitics after changing cell pins.'}
(w/'reports/probe50_electrical_violations.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='violations'},indent=2))
