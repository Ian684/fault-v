"""Bounded obstacle-aware M2-M5 repair with explicit legal M3 landing area."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,bisect,collections,functools,heapq,math,re,time,odb
from temporary_fixed_routes import primitives,encode_fixed
def repair_corner(design,db,b,out,normalize,connectivity):
    C=Path('/work/week25_closure');tech=db.getTech();net=b.findNet('net3347');name=net.getName();original=primitives(net.getWire())[0]
    qa=('S','met2',1580330,639370,1583550,639370,70,70);qz=('S','met2',1583550,639370,1583550,643450,70,70)
    assert original[qa]==original[qz]==1
    bounds=[1565000,620000,1605000,670000];cache=[]
    rect=lambda q:[q.xMin(),q.yMin(),q.xMax(),q.yMax()]
    hit=lambda q,r:q[0]<=r[2] and q[2]>=r[0] and q[1]<=r[3] and q[3]>=r[1]
    def add(layer,q,owner):
        if hit(q,bounds):cache.append([layer,*q,owner])
    for n in b.getNets():
        if n.getWire():
            assert n.getNonDefaultRule() is None
            for q in primitives(n.getWire())[0]:
                if q[0]=='S':
                    _,l,x1,y1,x2,y2,e1,e2=q;h=tech.findLayer(l).getWidth()//2
                    add(l,[x1-h,y1-e1,x2+h,y2+e2] if x1==x2 else [x1-e1,y1-h,x2+e2,y2+h],n.getName())
                elif q[0]=='R':add(q[1],list(q[2:6]),n.getName())
                elif q[0] in ('T','V'):
                    v=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);x,y=q[2:4]
                    if hit([x-2000,y-2000,x+2000,y+2000],bounds):
                        for z in v.getBoxes():add(z.getTechLayer().getName(),[z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y],n.getName())
        for sw in n.getSWires():
            for q in sw.getWires():
                if q.isVia():
                    v=q.getTechVia() or q.getBlockVia();x,y=q.getViaXY()
                    if hit([x-3000,y-3000,x+3000,y+3000],bounds):
                        for z in v.getBoxes():add(z.getTechLayer().getName(),[z.xMin()+x,z.yMin()+y,z.xMax()+x,z.yMax()+y],n.getName())
                else:add(q.getTechLayer().getName(),rect(q),n.getName())
    for i in b.getInsts():
        if not hit(rect(i.getBBox()),bounds):continue
        for p in i.getITerms():
            for l,q in p.getGeometries():add(l.getName(),rect(q),p.getNet().getName() if p.getNet() else '@pin')
        orient=str(i.getOrient());ox,oy=i.getLocation();mw=i.getMaster().getWidth();mh=i.getMaster().getHeight();assert orient in ('R0','MX','MY','R180')
        for q in i.getMaster().getObstructions():
            x1,y1,x2,y2=rect(q)
            if orient in ('MY','R180'):x1,x2=mw-x2,mw-x1
            if orient in ('MX','R180'):y1,y2=mh-y2,mh-y1
            add(q.getTechLayer().getName(),[ox+x1,oy+y1,ox+x2,oy+y2],'@obs')
    for q in b.getObstructions():add(q.getBBox().getTechLayer().getName(),rect(q.getBBox()),'@block_obs')
    signature=lambda v:tuple(sorted((z.getTechLayer().getName(),z.xMin(),z.yMin(),z.xMax(),z.yMax()) for z in v.getBoxes()))
    existing=defaultdict(list)
    for q in original:
        if q[0] in ('T','V'):
            v=tech.findVia(q[1]) if q[0]=='T' else b.findVia(q[1]);existing[q[2],q[3]].append(signature(v))
    specs=[]
    for v in tech.getVias():
        if v.getBottomLayer().getName() not in ('met1','met2','met3','met4'):continue
        boxes=[list(z) for z in signature(v)]
        if sum(l not in ('met1','met2','met3','met4','met5') for l,*_ in boxes)!=1:continue
        pads=[None] if not any(l=='met3' for l,*_ in boxes) else [('met3',-450,-150,450,150),('met3',-150,-450,150,450)]
        for index,pad in enumerate(pads):
            specs.append({'name':v.getName()+'@'+str(index),'actual':v.getName(),'lo':v.getBottomLayer().getName(),'hi':v.getTopLayer().getName(),'real':signature(v),'pad':pad,'boxes':boxes+([list(pad)] if pad else [])})
    byname={s['name']:s for s in specs};width={l:tech.findLayer(l).getWidth() for l in ('met1','met2','met3','met4','met5')}
    spacing={'met1':140,'via':170,'met2':140,'met3':300,'met4':300,'met5':1600,'via2':200,'via3':200,'via4':800}
    env={'collections':collections,'functools':functools,'heapq':heapq,'bisect':bisect,'math':math,'time':time,'spacing':spacing,'width':width,'layername':lambda n:'met'+str(n),'bucket':defaultdict(list),'data':{'vias':specs},'shapes':[],'existing':existing}
    raw=(C/'controls/li1_bridge_a_impl.py').read_text();tree=ast.parse(raw);names={'rebuild','clear','wireok','viaok','search'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    code='\n'.join(ast.get_source_segment(raw,n) for n in nodes)
    for f,size in [('clear',350000),('wireok',350000),('viaok',200000)]:code=code.replace('def '+f+'(',f'@functools.lru_cache({size})\ndef '+f+'(')
    code=code.replace('if n==net:continue','if n==net and l in width:continue').replace('time.monotonic()-began>180','time.monotonic()-began>60')
    needle="    xs=sorted(x for x in xs if loX<=x<=hiX);ys=sorted(y for y in ys if loY<=y<=hiY)"
    code=code.replace(needle,"    xs.update(x for x,y in existing if loX<=x<=hiX);ys.update(y for x,y in existing if loY<=y<=hiY)\n"+needle)
    exec(compile(code,'existing_bounded_upper_metal_planner','exec'),env)
    @functools.lru_cache(200000)
    def viaok(target,vi,x,y):
        s=specs[vi]
        if s['real'] in existing.get((x,y),[]):return True
        return all(env['clear'](target,l,x+a,y+bb,x+c,y+d) for l,a,bb,c,d in s['boxes'])
    env['viaok']=viaok
    def piece(layer,a,z):
        a,z=sorted((a,z));h=width[layer]//2;return ('S',layer,*a,*z,h,h)
    def install(g):encode_fixed(net.getWire(),g,tech,b);normalize(net.getWire());assert primitives(net.getWire())[0]==g
    def append_path(path):
        compact=[]
        for edge in path:
            if compact and not edge['via'] and not compact[-1]['via']:
                prev=compact[-1];a,z=prev['from'],prev['to'];end=edge['to']
                if z==edge['from'] and a[2]==z[2]==end[2] and (a[0]==z[0]==end[0] or a[1]==z[1]==end[1]):prev['to']=end;continue
            compact.append(dict(edge))
        added=Counter()
        for edge in compact:
            a,z=edge['from'],edge['to']
            if edge['via']:
                s=byname[edge['via']]
                if s['real'] in existing.get(tuple(a[:2]),[]):continue
                added['T',s['actual'],*a[:2]]+=1
                if s['pad']:
                    l,x1,y1,x2,y2=s['pad'];added['R',l,x1+a[0],y1+a[1],x2+a[0],y2+a[1]]=1
            else:added[piece('met'+str(a[2]),a[:2],z[:2])]+=1
        return compact,added
    print('UPPER_OBSTACLES_READY',len(cache),'via options',len(specs),flush=True)
    extra=[]
    options=[(1582090,641070),(1581630,642430),(1581170,643300),(1582550,640390),(1580630,643380)]
    for attempt,(px,ry) in enumerate(options):
        start=(px,639370,2);end=(1583550,ry,2);roi=[px-8000,639370-8000,1583550+8000,ry+8000]
        env['data']['region']=roi;env['shapes']=[q for q in cache if hit(q[1:5],roi)]+extra;env['rebuild']()
        path=env['search'](name,start,end)
        if path is None:continue
        base=original-Counter([qa,qz])+Counter([piece('met2',(1580330,639370),start[:2]),piece('met2',end[:2],(1583550,643450))])
        compact,added=append_path(path);install(base+added)
        design.getTritonRoute().clearDesign();report=out/f'astar_{attempt}.rpt'
        design.evalTclString('drt::check_drc -box {'+' '.join(map(str,roi))+'} -output_file '+str(report)+' -marker_name UpperObstacleRepair')
        text=report.read_text();rows=re.findall(r'violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = \(([-0-9.]+), ([-0-9.]+)\) - \(([-0-9.]+), ([-0-9.]+)\) on Layer ([^\n]+)',text);assert len(rows)==text.count('violation type:')
        missing,disconnected,count,components=connectivity(net);connected=not missing and not disconnected and components==1
        print('UPPER_ASTAR_TRIAL',attempt,len(rows),connected,flush=True)
        if not rows and connected:return {'net':name,'kind':'obstacle_aware_corner','original_segments':[qa,qz],'cut_start':start,'cut_end':end,'path':compact,'added_primitives':list(added.elements())}
        for kind,src,x1,y1,x2,y2,layer in rows:
            if layer in spacing:extra.append([layer,round(float(x1)*1000),round(float(y1)*1000),round(float(x2)*1000),round(float(y2)*1000),'@native_rejection'])
        install(original)
    return None
