"""Early read-only audit of the saved first insertion, before expensive route completion."""
from pathlib import Path
from collections import Counter
import hashlib,json,odb
R=Path('/work/routing')
source=R/'inputs/antenna_model_validated.odb'
path=R/'runs/routed_antenna_20261026_190111/1-openroad-detailedrouting/antenna_inserted_1.odb'
def load(p):
    d=odb.dbDatabase.create(); odb.read_db(d,str(p)); return d,d.getChip().getBlock()
d,b=load(path); rd,rb=load(source)
old={i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation())) for i in rb.getInsts()}
new={i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation())) for i in b.getInsts()}
changed=[n for n,v in old.items() if new.get(n)!=v]
diodes=set(new)-set(old); bad=[]; pg=Counter()
for name in diodes:
    i=b.findInst(name)
    assert i.getMaster().getName()=='sky130_fd_sc_hd__diode_2'
    for pin in i.getITerms():
        st=str(pin.getMTerm().getSigType())
        net=pin.getNet()
        if st in ['POWER','GROUND']:
            expected='VPWR' if st=='POWER' else 'VGND'
            if net is None or net.getName()!=expected: bad.append([name,pin.getMTerm().getName()])
            pg[st]+=1
assert not changed and not bad,(changed[:10],bad[:10])
receipt={'pass':True,'scope':'Saved pre-route insertion only; not final physical/antenna/timing acceptance','inserted_diodes':len(diodes),'unchanged_existing_cells':len(old),'changed_existing_cells':changed,'unconnected_or_wrong_PG_pins':bad,'connected_diode_PG_pins':dict(pg),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(R/'reports/antenna_model/first_insertion_audit.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
