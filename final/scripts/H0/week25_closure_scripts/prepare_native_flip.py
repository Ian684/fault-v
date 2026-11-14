from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/repair_native_upper.py').read_text().replace('native_upper_b','native_upper_e')
marker="done=False\nfor name in re.findall(r'net:([^\\s]+)',marker['srcs']):";assert code.count(marker)==1
flip='''done=False
n=b.findNet('net3347');geometry=primitives(n.getWire())[0]
qa=('S','met2',1584010,638690,1584010,639370,70,70)
qz=('S','met2',1584010,639370,1584470,639370,70,70)
assert geometry[qa]==geometry[qz]==1
points=[(1584010,638690),(1584470,638690),(1584470,639370)]
added=Counter(piece('met2',a,z) for a,z in zip(points,points[1:]));trial=geometry-Counter([qa,qz])+added;install(n,trial)
count=sum(check('flipped_corner',[1580000,635000,1588500,643500]).values());conn=connected(n) if count==0 else False
print('NATIVE_CORNER_FLIP',count,conn,flush=True)
if count==0 and conn:
    repairs.append({'net':'net3347','kind':'corner_flip','original_segments':[qa,qz],'points':points,'layer':'met2'});done=True
else:install(n,geometry)
for name in ([] if done else re.findall(r'net:([^\\s]+)',marker['srcs'])):
'''
code=code.replace(marker,flip)
p=C/'scripts/repair_native_flip.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_M2_CORNER_FLIP_PREPARED')
