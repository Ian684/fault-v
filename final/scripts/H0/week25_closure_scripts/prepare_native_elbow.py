from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/repair_native_upper.py').read_text().replace('native_upper_b','native_upper_c')
marker="done=False\nfor name in re.findall(r'net:([^\\s]+)',marker['srcs']):"
assert code.count(marker)==1
elbow='''done=False
n=b.findNet('net5547');geometry=primitives(n.getWire())[0]
qa=('S','met2',1579410,639370,1584010,639370,70,70)
qz=('S','met2',1584010,639370,1584010,657390,70,70)
assert geometry[qa]==geometry[qz]==1
for left in (1000,1380,2000,2500):
    for down in (1000,1360,2040,2500):
        p=(1584010-left,639370);r=(1584010,639370+down);corner=(1584010,639370)
        for top in (3,4):
            counter+=1;upper='met'+str(top)
            added=Counter([piece('met2',(1579410,639370),p),piece('met2',r,(1584010,657390)),piece(upper,p,corner),piece(upper,corner,r)])
            for x,y in (p,r):
                for lev in range(2,top):added['T',via_name[lev],x,y]+=1
            trial=geometry-Counter([qa,qz])+added;install(n,trial)
            roi=[p[0]-4000,p[1]-4000,r[0]+4000,r[1]+4000]
            count=sum(check('elbow_'+str(counter),roi).values());conn=connected(n) if count==0 else False
            attempts.append({'kind':'short_elbow','trial':counter,'net':'net5547','top':top,'native_local_DRC':count,'connected':conn})
            print('NATIVE_ELBOW_TRIAL',counter,top,count,conn,flush=True)
            if count==0 and conn:
                repairs.append({'net':'net5547','kind':'short_elbow','original_segments':[qa,qz],'cut_start':p,'cut_end':r,'corner':corner,'bridge_layer':upper});done=True;break
            install(n,geometry)
        if done:break
    if done:break
for name in ([] if done else re.findall(r'net:([^\\s]+)',marker['srcs'])):
'''
code=code.replace(marker,elbow)
p=C/'scripts/repair_native_elbow.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_M2_ELBOW_REPAIR_PREPARED')
