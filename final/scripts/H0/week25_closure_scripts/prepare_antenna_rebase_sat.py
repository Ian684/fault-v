from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/rebase_native_antenna.py').read_text().replace("out=C/'reports/antenna_rebase'","out=C/'reports/antenna_rebase_sat'").replace('/runtime_final/antenna_rebase.odb','/runtime_final/antenna_rebase_sat.odb').replace("C/'inputs/antenna_rebase.odb'","C/'inputs/antenna_rebase_sat.odb'")
start=code.index('seen=set()');end=code.index('assert fixed(b)==before',start)
loop='''from route_choice_sat import solve
clauses=[((n,True),(n,True)) for n in sorted(affected)]+[((n,False),(n,False)) for n in sorted(protected)]
def forbid(markers,choices):
    for kind,src,box,layer in markers:
        names=sorted(set(re.findall(r'net:([^\\s]+)',src)))
        assert 1<=len(names)<=2 and all(n in choices for n in names),(kind,src)
        literals=[(n,choices[n]!='native') for n in names]
        clauses.append((literals[0],literals[-1]))
seed=json.loads((C/'reports/antenna_rebase/progress.json').read_text())
prior={n:'native' if n in affected else 'original' for n in native_wires}
for row in seed['history']:
    forbid(row['markers'],prior)
    changes={}
    for kind,src,box,layer in row['markers']:
        names=set(re.findall(r'net:([^\\s]+)',src))
        if len(names)==1:
            n=next(iter(names));changes[n]='native' if prior[n]=='original' else 'original';continue
        can_native={n for n in names if n not in protected and n not in affected and prior[n]=='original'}
        for n in can_native:changes[n]='native'
        if not can_native:
            for n in names:
                if n not in affected and n not in protected and prior[n]=='native':changes[n]='original'
    prior.update(changes)
for iteration in range(48):
    solution=solve(clauses)
    if solution is None:
        (out/'unsatisfiable.json').write_text(json.dumps({'clauses':clauses,'accepted_for_final':False,'scope':'Observed pairwise constraints cannot be satisfied by whole-wire source choices with these hard assignments. Local geometry repair is required.'},indent=2)+'\\n')
        raise AssertionError('Whole-wire source constraints unsatisfiable')
    desired={n:'native' if solution.get(n,n in affected) else 'original' for n in selected}
    for n,v in desired.items():
        if selected[n]!=v:assign(n,v)
    markers=check(iteration);state=sorted(n for n,v in selected.items() if v=='native' and n not in affected)
    history.append({'iteration':iteration,'non_partition_planning_markers':len(markers),'native_neighbor_count':len(state),'native_neighbors':state,'markers':markers})
    (out/'progress.json').write_text(json.dumps({'history':history,'clauses':clauses,'accepted_for_final':False},indent=2)+'\\n')
    print('SAT_ROUTE_SELECTION',iteration,len(markers),'native neighbors',len(state),'clauses',len(clauses),flush=True)
    if not markers:break
    forbid(markers,selected)
else:raise AssertionError('SAT route-selection bound reached')
'''
code=code[:start]+loop+code[end:]
p=C/'scripts/rebase_native_antenna_sat.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('SAT_ROUTE_SELECTION_PREPARED')
