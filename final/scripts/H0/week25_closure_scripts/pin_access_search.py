"""Seed M1 routing from every legal 5nm mcon centre inside the current diode pin."""
import collections,heapq,time

def make_pin_access_search(e):
    def search(net,start,end):
        region=e['data']['region'];loX,loY,hiX,hiY=region;vias=e['data']['vias'];pins=e['allowed_pin_rects'];h=e['width']['li1']//2
        assert start[2]==0 and end[2] in (1,2)
        seeds={};seed_paths={};legal=0
        def prefix_to(x,y,vname):
            p=start;edges=[]
            for z in ((x,start[1],0),(x,y,0)):
                if p!=z:
                    if not e['wireok'](net,'li1',*p[:2],*z[:2]):return None
                    edges.append({'from':p,'to':z,'via':None});p=z
            edges.append({'from':p,'to':(x,y,1),'via':vname});return edges
        for a,c,z,f in pins:
            if not (a+h<=start[0]<=z-h and c+h<=start[1]<=f-h):continue
            for x in range(((a+h+4)//5)*5,z-h+1,5):
                for y in range(((c+h+4)//5)*5,f-h+1,5):
                    for vi,v in enumerate(vias):
                        if v['lo']!='li1' or v['hi']!='met1' or not e['viaok'](net,vi,x,y):continue
                        prefix=prefix_to(x,y,v['name'])
                        if prefix is None:continue
                        s=(x,y,1);cost=abs(x-start[0])+abs(y-start[1])+500;legal+=1
                        if cost<seeds.get(s,10**30):seeds[s]=cost;seed_paths[s]=prefix
                        break
        print('LEGAL_IN_PIN_MCON_CENTRES',net,len(seeds),'raw',legal,flush=True)
        if not seeds:return None
        xs=set(range((loX//50)*50,hiX+1,50));ys=set(range((loY//50)*50,hiY+1,50));xs.add(end[0]);ys.add(end[1])
        xs.update(s[0] for s in seeds);ys.update(s[1] for s in seeds)
        for l,a,c,z,f,n in e['shapes']:
            if n==net or l not in ('met1','met2') or a>hiX or z<loX or c>hiY or f<loY:continue
            pad=e['spacing'][l]+e['width'][l]//2;xs.update(v for v in (a-pad,z+pad) if loX<=v<=hiX);ys.update(v for v in (c-pad,f+pad) if loY<=v<=hiY)
        xs=sorted(v for v in xs if loX<=v<=hiX);ys=sorted(v for v in ys if loY<=v<=hiY);xi={v:i for i,v in enumerate(xs)};yi={v:i for i,v in enumerate(ys)}
        choices=collections.defaultdict(list)
        for vi,v in enumerate(vias):
            if v['lo']=='met1' and v['hi']=='met2':choices[1].append((2,vi));choices[2].append((1,vi))
        cost=dict(seeds);prev={};q=[]
        for s,c in seeds.items():heapq.heappush(q,(c+abs(s[0]-end[0])+abs(s[1]-end[1])+abs(s[2]-end[2])*500,c,s))
        began=time.monotonic();count=0
        while q:
            _,c,s=heapq.heappop(q)
            if c!=cost[s]:continue
            count+=1
            if s==end:
                path=[]
                while s in prev:
                    old,via=prev[s];path.append({'from':old,'to':s,'via':via});s=old
                path.reverse();path=seed_paths[s]+path;print('PIN_ACCESS_PATH_FOUND',net,count,c,len(path),flush=True);return path
            if count>1200000 or time.monotonic()-began>90:print('PIN_ACCESS_SEARCH_BOUND',net,count,flush=True);return None
            x,y,L=s;l='met'+str(L);adj=[]
            for axis,delta in ((0,-1),(0,1),(1,-1),(1,1)):
                values=xs if axis==0 else ys;i=(xi[x] if axis==0 else yi[y])+delta
                if not 0<=i<len(values):continue
                z=(values[i],y,L) if axis==0 else (x,values[i],L)
                if e['wireok'](net,l,x,y,z[0],z[1]):adj.append((z,abs(x-z[0])+abs(y-z[1]),None))
            for zL,vi in choices[L]:
                if e['viaok'](net,vi,x,y):adj.append(((x,y,zL),500,vias[vi]['name']))
            for z,delta,v in adj:
                nc=c+delta
                if nc<cost.get(z,10**30):
                    cost[z]=nc;prev[z]=(s,v);heur=abs(z[0]-end[0])+abs(z[1]-end[1])+abs(z[2]-end[2])*500;heapq.heappush(q,(nc+heur,nc,z))
        print('NO_IN_PIN_M1_M2_ROUTE',net,count,flush=True);return None
    return search
