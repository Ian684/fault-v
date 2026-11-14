"""Exercise branches, vias, endpoint extensions and patches without modifying saved ODBs."""
from pathlib import Path
import odb
R=Path(__file__).resolve().parents[1]
d=odb.dbDatabase.create();odb.read_db(d,str(R/"inputs/fault_v_asic_top.odb"))
b=d.getChip().getBlock();tech=d.getTech();layer=tech.findLayer("met2")
via=next(v for v in tech.getVias() if v.getBottomLayer().getName()=="met2" and v.getTopLayer().getName()=="met3")
for extension,patch in [(False,False),(True,False),(False,True),(True,True)]:
    net=odb.dbNet_create(b,f"decoder_probe_{extension}_{patch}")
    wire=odb.dbWire_create(net)
    e=odb.dbWireEncoder();e.begin(wire);e.newPath(layer,"ROUTED")
    e.addPoint(100000,100000);j=e.addPoint(110000,100000)
    if extension:e.addPoint(120000,100000,500,0)
    else:e.addPoint(120000,100000)
    if patch:e.addRect(-200,-200,200,200)
    e.newPath(j);e.addPoint(110000,120000)
    e.newPath(j);e.addTechVia(via);e.addPoint(110000,80000);e.end()
    dec=odb.dbWireDecoder();dec.begin(wire)
    points={};previous=None;total=0
    while True:
        op=dec.next()
        if op==dec.END_DECODE:break
        if op==dec.PATH:previous=None
        elif op==dec.JUNCTION:previous=points[dec.getJunctionValue()]
        elif op in [dec.POINT,dec.POINT_EXT]:
            p=tuple((dec.getPoint_ext() if op==dec.POINT_EXT else dec.getPoint())[:2])
            if previous is not None:total+=abs(p[0]-previous[0])+abs(p[1]-previous[1])
            previous=p;points[dec.getJunctionId()]=p
        elif op in [dec.TECH_VIA,dec.VIA]:points[dec.getJunctionId()]=previous
    expected=60000+(500-layer.getWidth()//2 if extension else 0)
    print("extended",extension,"patch",patch,"centerline",total,"native",wire.getLength(),"expected_native",expected)
    assert total==60000 and wire.getLength()==expected
print("BRANCH / VIA / POINT_EXT / PATCH LENGTH SELF-CHECKS PASSED")
