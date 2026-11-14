from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/repair_native_upper.py').read_text().replace('native_upper_b','native_upper_d')
marker="done=False\nfor name in re.findall(r'net:([^\\s]+)',marker['srcs']):";assert code.count(marker)==1
dogleg='''done=False
n=b.findNet('net5547');geometry=primitives(n.getWire())[0]
qa=('S','met2',1579410,639370,1584010,639370,70,70)
qz=('S','met2',1584010,639370,1584010,657390,70,70)
assert geometry[qa]==geometry[qz]==1
for dx in (460,920,1380,1840,2300,2760,3220,3680):
    for dy in (340,680,1020,1360,2040,2720):
        sx=1584010-dx;sy=639370+dy;counter+=1
        points=[(1579410,639370),(sx,639370),(sx,sy),(1584010,sy),(1584010,657390)]
        added=Counter(piece('met2',a,z) for a,z in zip(points,points[1:]));trial=geometry-Counter([qa,qz])+added;install(n,trial)
        roi=[sx-4000,639370-4000,1584010+4000,sy+4000]
        count=sum(check('dogleg_'+str(counter),roi).values());conn=connected(n) if count==0 else False
        attempts.append({'kind':'short_dogleg','trial':counter,'net':'net5547','points':points,'native_local_DRC':count,'connected':conn})
        print('NATIVE_DOGLEG_TRIAL',counter,dx,dy,count,conn,flush=True)
        if count==0 and conn:
            repairs.append({'net':'net5547','kind':'short_dogleg','original_segments':[qa,qz],'points':points,'layer':'met2'});done=True;break
        install(n,geometry)
    if done:break
for name in ([] if done else re.findall(r'net:([^\\s]+)',marker['srcs'])):
'''
code=code.replace(marker,dogleg)
p=C/'scripts/repair_native_dogleg.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_M2_DOGLEG_PREPARED')
