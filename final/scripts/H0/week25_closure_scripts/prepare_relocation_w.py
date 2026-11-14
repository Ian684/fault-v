from pathlib import Path
import json,hashlib
C=Path(__file__).resolve().parents[1]
snapshot=(C/'reports/native_group_v/progress.json').read_bytes();data=json.loads(snapshot)
assert len(data['accepted'])>=2 and data['relocations'] and not data['failed_diodes']
control=C/'controls/relocation_v_partial.json';assert not control.exists();control.write_bytes(snapshot)
code=(C/'scripts/append_native_group_v.py').read_text().replace('native_group_v','native_group_w')
needle="relocating={'ANTENNA_7559','ANTENNA_7560','ANTENNA_7567','ANTENNA_7572'}";assert code.count(needle)==1
code=code.replace(needle,needle+'''
partial=json.loads((C/'controls/relocation_v_partial.json').read_text())
for row in partial['relocations']:
    diode=b.findInst(row['diode']);assert list(diode.getLocation())==row['old_location'];diode.setLocation(*row['new_location'])
''')
code=code.replace('accepted=[];paths=defaultdict(list);failed=[];relocations=[]',"accepted=[];paths=defaultdict(list);failed=[];relocations=partial['relocations'].copy()")
needle="prior=json.loads((C/'reports/native_group_r/incomplete.json').read_text())['accepted'];assert len(prior)==1";assert code.count(needle)==1
code=code.replace(needle,"prior=partial['accepted'];assert len(prior)>=2")
needle="print('REPLAYED_R_INSIDE_PIN_BRANCH',flush=True)";assert code.count(needle)==1
code=code.replace(needle,"""for row in partial['relocations']:
    for shape in cell_geometry(b.findInst(row['diode'])):add(shape[0],shape[1:5],shape[-1])
peers=defaultdict(list)
for inst in b.getInsts():
    if inst.getName() not in relocating and inst.getMaster().getName()=='sky130_fd_sc_hd__diode_2' and inst.findITerm('DIODE').getPrefAccessPoints():peers[str(inst.getOrient())].append(inst)
print('REPLAYED_CHECKED_PARTIAL_BRANCHES',len(prior),flush=True)""")
code=code.replace("    if row['diode'] not in relocating:continue", "    if row['diode'] not in relocating or any(r['diode']==row['diode'] for r in accepted):continue")
old="""        if str(rr.getOrient())!=orient or abs(y+py-goal[1])>15000 or (y-old[1])%340:continue
        x0=q[0]+round((goal[0]-px-q[0])/460)*460
"""
new="""        rorient=str(rr.getOrient())
        if rorient not in ('R0','MX') or abs(y+1300-goal[1])>15000 or (y-old[1])%340:continue
        peer=next((p for p in peers[rorient] if (q[0]-p.getLocation()[0])%460==0 and (y-p.getLocation()[1])%340==0),None)
        assert peer,('Missing same-phase diode access peer',rorient,y)
        points=list(peer.findITerm('DIODE').getPrefAccessPoints());px,py=points[0].getPoint()
        x0=q[0]+round((goal[0]-px-q[0])/460)*460
"""
assert code.count(old)==1;code=code.replace(old,new)
code=code.replace('candidates.append((distance,x,y))',"candidates.append((distance,x,y,rorient,peer.getName()))")
code=code.replace('for index,(distance,x,y) in enumerate(candidates[:80]):\n        diode.setLocation(x,y)', '''for index,(distance,x,y,rorient,peername) in enumerate(candidates[:100]):
        peer=b.findInst(peername);diode.setOrient(rorient);diode.setLocation(x,y);diode.setPinAccessIdx(peer.getPinAccessIdx())
        for pin in diode.getITerms():
            pin.clearPrefAccessPoints()
            for a in peer.findITerm(pin.getMTerm().getName()).getPrefAccessPoints():pin.setAccessPoint(a.getMPin(),a)
        own=list(diode.findITerm('DIODE').getPrefAccessPoints());px,py=own[0].getPoint()
        assert all(any(l.getName()==a.getLayer().getName() and z.xMin()<=x+a.getPoint()[0]<=z.xMax() and z.yMin()<=y+a.getPoint()[1]<=z.yMax() for l,z in diode.findITerm('DIODE').getGeometries()) for a in own)''')
code=code.replace("'orientation':orient,'same_phase_and_empty_native_row_slot'", "'old_orientation':orient,'orientation':rorient,'native_access_peer':peername,'same_phase_and_empty_native_row_slot'")
code=code.replace("expected[row['diode']]=(old[0],old[1],tuple(row['new_location']),old[3])", "assert old[1]==row.get('old_orientation',row['orientation']);expected[row['diode']]=(old[0],row['orientation'],tuple(row['new_location']),old[3])")
code=code.replace("'pin_access_method':'5nm mcon centre enumeration inside the unchanged diode pin; M1/M2 search only'", "'pin_access_method':'four added passive diodes may move/flip into empty matching native rows; real same-phase/orientation native AP peer; 5nm mcon and M1/M2 only'")
p=C/'scripts/append_native_group_w.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,newline='\n')
sh=(C/'scripts/run_native_group_v.sh').read_text().replace('native_group_v','native_group_w').replace('native-group-v','native-group-w').replace('antenna_native_v','antenna_native_w')
(C/'scripts/run_native_group_w.sh').write_text(sh,newline='\n');print('W_BOTH_ROW_ORIENTATIONS_PREPARED',hashlib.sha256(snapshot).hexdigest(),len(data['accepted']))
