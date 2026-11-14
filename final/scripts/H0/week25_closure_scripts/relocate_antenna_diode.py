"""Move one newly inserted passive diode to a verified free, same-phase native row."""
from pathlib import Path
import hashlib,json,re,shutil
def relocate(design,db,b,targets,C,tag):
    diode=b.findInst('ANTENNA_7568');gate=b.findInst('_39369_').findITerm('B1')
    assert diode.getMaster().getName()=='sky130_fd_sc_hd__diode_2'
    assert diode.findITerm('DIODE').getNet().getName()==gate.getNet().getName()=='net6033'
    old=tuple(diode.getLocation());orient=str(diode.getOrient());w=diode.getMaster().getWidth();h=diode.getMaster().getHeight()
    gx,gy=b.findInst('_39369_').getLocation();ap=list(gate.getPrefAccessPoints());assert len(ap)>0
    tx,ty=ap[0].getPoint();tx+=gx;ty+=gy
    own=list(diode.findITerm('DIODE').getPrefAccessPoints());assert own
    px,py=own[0].getPoint()
    boxes=[(i.getBBox().xMin(),i.getBBox().yMin(),i.getBBox().xMax(),i.getBBox().yMax()) for i in b.getInsts() if i.getName()!=diode.getName()]
    candidates=[]
    for row in b.getRows():
        if str(row.getOrient())!=orient:continue
        q=row.getBBox();y=q.yMin()
        if abs(y+py-ty)>6000:continue
        x0=q.xMin()+round((tx-px-q.xMin())/460)*460
        for offset in range(-14,15):
            x=x0+offset*460
            if x<q.xMin() or x+w>q.xMax() or (x-old[0])%460 or (y-old[1])%340:continue
            if any(x<a2 and x+w>a1 and y<b2 and y+h>b1 for a1,b1,a2,b2 in boxes):continue
            candidates.append((abs(x+px-tx)+abs(y+py-ty),x,y))
    candidates=sorted(set(candidates));assert candidates,'No legal nearby row slot'
    variant=tag[-1];assert re.fullmatch('[a-z]',variant)
    folder=C/'reports'/('antenna_relocation_'+variant);folder.mkdir(parents=True,exist_ok=False)
    chosen=None;attempts=[]
    for index,(distance,x,y) in enumerate(candidates[:40]):
        diode.setLocation(x,y)
        for a in own:
            ax,ay=a.getPoint()
            assert any(l.getName()==a.getLayer().getName() and z.xMin()<=x+ax<=z.xMax() and z.yMin()<=y+ay<=z.yMax() for l,z in diode.findITerm('DIODE').getGeometries())
        report=folder/f'position_{index:02}.rpt';design.getTritonRoute().clearDesign()
        roi=[x-4000,y-4000,x+w+4000,y+h+4000]
        design.evalTclString('drt::check_drc -box {'+' '.join(map(str,roi))+'} -output_file '+str(report)+' -marker_name PassiveDiodePlacement')
        count=report.read_text().count('violation type:');attempts.append({'location':[x,y],'native_DRC':count,'distance_to_gate_AP_dbu':distance})
        if count==0:chosen=(x,y);break
    assert chosen,'No independently DRC-clean passive diode position'
    design.evalTclString('check_placement -verbose')
    for row in targets:
        if row['diode']=='ANTENNA_7568':row['access_points']=[(chosen[0]+a.getPoint()[0],chosen[1]+a.getPoint()[1],a.getLayer().getName()) for a in own]
    native=Path('/runtime_final/antenna_reference_'+variant+'.odb');dest=C/'inputs'/native.name;assert not native.exists() and not dest.exists()
    import odb
    odb.write_db(db,str(native))
    with native.open('rb') as f,dest.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
    def sha(p):
        with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    assert sha(native)==sha(dest)
    record={'cell':'ANTENNA_7568','master':'sky130_fd_sc_hd__diode_2','net':'net6033','old_location':old,'new_location':chosen,'orientation':orient,'same_native_AP_site_phase':True,'native_placement_pass':True,'native_local_DRC':0,'reference_ODB':str(native),'reference_sha256':sha(native),'attempts':attempts,'accepted_for_final':False,'scope':'Only this new passive diode relocated. Final original-cell/graph/PG binding, full DRC/connectivity/antenna/core-LVS/RCX/STA/activity/IR remain required.'}
    (C/'reports'/('antenna_relocation_'+variant+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    print('PASSIVE_DIODE_RELOCATED',old,chosen,'gate_AP',tx,ty,flush=True)
    return record
