# Conservative geometry is a search filter; the native DRC checker remains authoritative.
import bisect, math, time
spacing={'met1':140,'met2':140,'met3':300,'met4':300,'met5':1600,'via':170,'via2':200,'via3':200,'via4':800}
width={l:tech.findLayer(l).getWidth() for l in ('met1','met2','met3','met4','met5')}
bucket=collections.defaultdict(list)

def rebuild():
    bucket.clear()
    for l,x1,y1,x2,y2,n in shapes:
        if l not in spacing:continue
        for x in range(x1//1000,x2//1000+1):
            for y in range(y1//1000,y2//1000+1):bucket[l,x,y].append((x1,y1,x2,y2,n))
    clear.cache_clear();wireok.cache_clear();viaok.cache_clear()

@functools.lru_cache(350000)
def clear(net,l,x1,y1,x2,y2):
    sp=spacing[l]
    for bx in range((x1-sp)//1000,(x2+sp)//1000+1):
        for by in range((y1-sp)//1000,(y2+sp)//1000+1):
            for a,c,z,f,n in bucket.get((l,bx,by),[]):
                if n==net:continue
                dx=max(a-x2,x1-z,0);dy=max(c-y2,y1-f,0)
                if dx*dx+dy*dy<sp*sp:return False
    return True

@functools.lru_cache(350000)
def wireok(net,l,x1,y1,x2,y2):
    h=width[l]//2
    return clear(net,l,min(x1,x2)-h,min(y1,y2)-h,max(x1,x2)+h,max(y1,y2)+h)

@functools.lru_cache(200000)
def viaok(net,vi,x,y):
    return all(clear(net,l,x+a,y+b,x+c,y+d) for l,a,b,c,d in data['vias'][vi]['boxes'])

def search(net,start,end):
    loX,loY,hiX,hiY=data['region']
    # Endpoint coordinates and nearby obstacle boundaries preserve narrow legal channels.
    xs=set(range((loX//50)*50,hiX+1,50));ys=set(range((loY//50)*50,hiY+1,50))
    xs.update((start[0],end[0]));ys.update((start[1],end[1]))
    for l,a,c,z,f,n in shapes:
        if n==net or l not in width or a>hiX or z<loX or c>hiY or f<loY:continue
        pad=spacing[l]+width[l]//2
        xs.update(v for v in (a-pad,z+pad) if loX<=v<=hiX)
        ys.update(v for v in (c-pad,f+pad) if loY<=v<=hiY)
    xs=sorted(x for x in xs if loX<=x<=hiX);ys=sorted(y for y in ys if loY<=y<=hiY)
    xidx={x:i for i,x in enumerate(xs)};yidx={y:i for i,y in enumerate(ys)}
    choices=collections.defaultdict(list)
    for vi,v in enumerate(data['vias']):
        if sum(l not in width for l,*_ in v['boxes'])!=1:continue
        if len([l for l,*_ in v['boxes'] if l not in width])!=1:continue
        lo=int(v['lo'][-1]);hi=int(v['hi'][-1]);choices[lo].append((hi,vi));choices[hi].append((lo,vi))
    q=[(0,0,start)];cost={start:0};prev={};count=0;began=time.monotonic()
    while q:
        _,c,s=heapq.heappop(q)
        if c!=cost[s]:continue
        count+=1
        if s==end:
            path=[]
            while s!=start:
                old,via=prev[s];path.append({'from':old,'to':s,'via':via});s=old
            path.reverse();print('FOUND',net,'visited',count,'cost',c,'edges',len(path),flush=True);return path
        if count>600000 or time.monotonic()-began>180:
            print('SEARCH_BOUND',net,count,flush=True);return None
        x,y,L=s;l='met'+str(L);xi=xidx[x];yi=yidx[y];adj=[]
        for axis,offset in ((0,-1),(0,1),(1,-1),(1,1)):
            arr=xs if axis==0 else ys;i=(xi if axis==0 else yi)+offset
            if not 0<=i<len(arr):continue
            z=(arr[i],y,L) if axis==0 else (x,arr[i],L)
            if wireok(net,l,x,y,z[0],z[1]):adj.append((z,abs(x-z[0])+abs(y-z[1]),None))
        for zL,vi in choices[L]:
            if viaok(net,vi,x,y):adj.append(((x,y,zL),500,data['vias'][vi]['name']))
        for z,delta,v in adj:
            nc=c+delta
            if nc<cost.get(z,1e30):
                cost[z]=nc;prev[z]=(s,v);h=abs(z[0]-end[0])+abs(z[1]-end[1])+abs(z[2]-end[2])*500
                heapq.heappush(q,(nc+h,nc,z))
    print('NO_PATH',net,count,dict(collections.Counter(z[2] for z in cost)),flush=True);return None
