"""Fill only native-reported same-net gaps, retaining strict physical rechecks."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs_c.py').read_text().replace('antenna_stubs_c','antenna_stubs_d').replace('reports/antenna_stubs_a/incomplete.json','reports/antenna_stubs_c/incomplete.json')
marker='accepted=[];paths=defaultdict(list)'
assert code.count(marker)==1
helpers='''def append_patches(net,patches):
    e=odb.dbWireEncoder();e.append(net.getWire());result=Counter()
    for q in patches:
        _,layer,x1,y1,x2,y2=q
        assert x1<x2 and y1<y2 and layer in width
        e.newPath(tech.findLayer(layer),'ROUTED');e.addPoint(x1,y1);e.addRect(0,0,x2-x1,y2-y1);result[q]+=1
    e.end();return result
def repair_gaps(net,baseline,after,roi,tag):
    additions=Counter()
    for iteration in range(6):
        new=after-baseline
        if not new:break
        if any(kind not in ('Metal Spacing','NS Metal','Min Hole') or set(re.findall(r'net:([^\\s]+)',src))!={net.getName()} for kind,src,box in new):break
        patches=[]
        for kind,src,box in new:
            m=re.fullmatch(r'\\(([-0-9.]+), ([-0-9.]+)\\) - \\(([-0-9.]+), ([-0-9.]+)\\) on Layer (\\w+)',box);assert m,box
            x1,y1,x2,y2=[round(float(v)*1000) for v in m.groups()[:4]];layer=m[5]
            if layer not in width:return additions,after
            q=('R',layer,x1-5,y1-5,x2+5,y2+5)
            assert roi[0]<=q[2]<q[4]<=roi[2] and roi[1]<=q[3]<q[5]<=roi[3]
            patches.append(q)
        additions+=append_patches(net,patches)
        updated=check(tag+f'_patch{iteration}',roi)
        if updated==after:after=updated;break
        after=updated
    return additions,after
'''
code=code.replace(marker,helpers+marker)
marker="        after=check(row['diode']+f'_trial{trial}',roi)"
assert code.count(marker)==1
code=code.replace(marker,marker+"\n        patches,after=repair_gaps(net,current,after,roi,row['diode']+f'_trial{trial}')\n        added+=patches\n        assert primitives(net.getWire())[0]==original+added")
marker='        for prior in paths[name]:append(net,prior)'
assert code.count(marker)==1
code=code.replace(marker,marker+"\n        previous_patches=[tuple(q) for record in accepted if record['net']==name for q in record['added_primitives'] if q[0]=='R']\n        if previous_patches:append_patches(net,previous_patches)")
p=C/'scripts/append_antenna_stubs_d.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_GAP_REPAIR_STUB_D_PREPARED')
