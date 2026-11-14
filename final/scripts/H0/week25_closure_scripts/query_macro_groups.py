from pathlib import Path
import ast,ctypes,json,odb
root=Path('/work/week25_closure');db=odb.dbDatabase.create();odb.read_db(db,str(root/'inputs/cached_guided.odb'));b=db.getChip().getBlock()
tree=ast.parse(Path('/work/routing/scripts/inspect_s0_access.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='header')
ns={'C':ctypes};exec(compile(ast.Module(body=[node],type_ignores=[]),'existing_readonly_vector_audit','exec'),ns);header=ns['header']
known={int(a.this):a for a in b.getAccessPoints()};print('KNOWN_ACCESS_POINTS',len(known),flush=True)
for inst in b.getInsts():
    if inst.getMaster().isBlock():
        for pin in inst.getITerms():
            if pin.getNet() and str(pin.getMTerm().getSigType()) not in ('POWER','GROUND'):
                for mpin in pin.getMTerm().getMPins():
                    raw=mpin.getPinAccess();start,count=header(int(raw),24,1000)
                    sizes=[]
                    for index in range(count):
                        begin,length=header(start+index*24,8,10000);sizes.append(length)
                        if index==inst.getPinAccessIdx():
                            addresses=list((ctypes.c_void_p*length).from_address(begin)) if length else []
                            assert all(a in known for a in addresses)
                            print('SELECTED_POINTS',[(known[a].getLayer().getName(),known[a].getPoint()) for a in addresses[:3]])
                    print('MACRO_GROUPS',inst.getName(),pin.getMTerm().getName(),inst.getPinAccessIdx(),count,sizes,flush=True)
                break
        break
