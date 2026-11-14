"""Solve pairwise route-source conflicts with explicit original/native literals."""
def solve(clauses):
    names=sorted({n for clause in clauses for n,v in clause});index={n:i for i,n in enumerate(names)}
    graph=[[] for _ in range(2*len(names))];reverse=[[] for _ in graph]
    def literal(pair):n,v=pair;return 2*index[n]+(0 if v else 1)
    for a,b in clauses:
        x,y=literal(a),literal(b)
        for src,dst in ((x^1,y),(y^1,x)):graph[src].append(dst);reverse[dst].append(src)
    seen=set();order=[]
    for root in [v for i in range(len(names)) for v in (2*i+1,2*i)]:
        if root in seen:continue
        seen.add(root);stack=[(root,0)]
        while stack:
            v,pos=stack[-1]
            if pos<len(graph[v]):
                nxt=graph[v][pos];stack[-1]=(v,pos+1)
                if nxt not in seen:seen.add(nxt);stack.append((nxt,0))
            else:order.append(v);stack.pop()
    components={};number=0
    for root in reversed(order):
        if root in components:continue
        stack=[root];components[root]=number
        while stack:
            v=stack.pop()
            for nxt in reverse[v]:
                if nxt not in components:components[nxt]=number;stack.append(nxt)
        number+=1
    if any(components[2*i]==components[2*i+1] for i in range(len(names))):return None
    result={n:components[2*i]>components[2*i+1] for n,i in index.items()}
    assert all(result[a[0]]==a[1] or result[b[0]]==b[1] for a,b in clauses)
    return result

assert solve([(('a',True),('a',True)),(('b',False),('b',False))])=={'a':True,'b':False}
assert solve([(('a',True),('a',True)),(('a',False),('a',False))]) is None
assert solve([(('a',False),('b',True)),(('a',True),('a',True))])=={'a':True,'b':True}
