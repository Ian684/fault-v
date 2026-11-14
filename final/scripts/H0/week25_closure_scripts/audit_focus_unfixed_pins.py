from pathlib import Path
import ast,ctypes,json,odb
C=Path('/work/week25_closure');db=odb.dbDatabase.create();odb.read_db(db,str(Path('/runtime/focus_unfixed.odb')));b=db.getChip().getBlock()
tree=ast.parse(Path('/work/routing/scripts/inspect_s0_access.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='header')
namespace={'C':ctypes};exec(compile(ast.Module(body=[node],type_ignores=[]),'existing_readonly_vector_audit','exec'),namespace);header=namespace['header']
# shortcut: pinned x86_64 vector ABI read only; replace when nested-vector bindings are exposed.
known={int(a.this):a for a in b.getAccessPoints()};macro_cache={}
errors=[];missing=[];checked=0;point_count=0;macro_pin_count=0
for inst in b.getInsts():
    x,y=inst.getLocation()
    for pin in inst.getITerms():
        net=pin.getNet()
        if net is None or str(pin.getMTerm().getSigType()) in ('POWER','GROUND'):continue
        if len(net.getITerms())+len(net.getBTerms())<2:continue
        checked+=1;points=list(pin.getPrefAccessPoints())
        if not points and inst.getMaster().isBlock():
            macro_pin_count+=1
            for mpin in pin.getMTerm().getMPins():
                key=int(mpin.this)
                if key not in macro_cache:
                    raw=mpin.getPinAccess();start,count=header(int(raw),24,1000);groups=[]
                    for index in range(count):
                        begin,length=header(start+index*24,8,10000)
                        addresses=list((ctypes.c_void_p*length).from_address(begin)) if length else []
                        assert all(address in known for address in addresses)
                        groups.append([known[address] for address in addresses])
                    macro_cache[key]=groups
                groups=macro_cache[key];assert inst.getPinAccessIdx()<len(groups)
                points+=groups[inst.getPinAccessIdx()]
        if not points:missing.append(inst.getName()+'/'+pin.getMTerm().getName())
        for point in points:
            point_count+=1;ax,ay=point.getPoint();layer=point.getLayer().getName()
            if not any(l.getName()==layer and q.xMin()<=x+ax<=q.xMax() and q.yMin()<=y+ay<=q.yMax() for l,q in pin.getGeometries()):
                errors.append({'pin':inst.getName()+'/'+pin.getMTerm().getName(),'point':[layer,x+ax,y+ay]})
result={'connected_signal_pins_checked':checked,'native_points_checked':point_count,'macro_pins_using_indexed_native_candidates':macro_pin_count,'missing':missing,'outside_actual_geometry':errors,'all_native_preferences_valid':not missing and not errors}
(C/'reports/focus_unfixed_all_pins.json').write_text(json.dumps(result,indent=2)+'\n')
assert checked>100000 and not missing and not errors,(checked,len(missing),len(errors))
print(json.dumps(result,indent=2),flush=True)
