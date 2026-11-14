from pathlib import Path
import json,odb
C=Path('/work/week25_closure');names=set(json.loads((C/'reports/minimal_input.json').read_text())['resized'])
files={'baseline':Path('/work/week25_front/runs/fill_only_20261029_a/1-openroad-fillinsertion/fault_v_asic_top.odb'),'changed_input':C/'inputs/minimal_partial.odb','neighbor_input':C/'inputs/neighbor_guided.odb'}
for tag in ('a','b'):
    paths=sorted((C/f'runs/minimal_route_{tag}/1-openroad-detailedrouting').glob('drt_iter*.odb'),key=lambda p:p.stat().st_mtime_ns)
    if len(paths)>=2:files[f'route_{tag}']=paths[-2]
result={}
for label,path in files.items():
    db=odb.dbDatabase.create();odb.read_db(db,str(path));b=db.getChip().getBlock();errors=[];missing=[];checked=0
    for name in names:
        inst=b.findInst(name);assert inst is not None
        x,y=inst.getLocation()
        for pin in inst.getITerms():
            if str(pin.getMTerm().getSigType()) in ('POWER','GROUND'):continue
            checked+=1;points=pin.getPrefAccessPoints()
            if not points:missing.append(name+'/'+pin.getMTerm().getName())
            for point in points:
                ax,ay=point.getPoint();layer=point.getLayer().getName()
                if not any(l.getName()==layer and q.xMin()<=x+ax<=q.xMax() and q.yMin()<=y+ay<=q.yMax() for l,q in pin.getGeometries()):
                    errors.append({'pin':name+'/'+pin.getMTerm().getName(),'master':inst.getMaster().getName(),'point':[layer,x+ax,y+ay]})
    result[label]={'source':str(path),'checked':checked,'missing':missing,'outside_actual_pin':errors}
    if label=='baseline':assert not errors and not missing
    if label=='changed_input':
        print('SHAPE_ITERATOR',hasattr(odb,'dbWireShapeItr'),hasattr(odb,'dbShape'))
        for name in ('sky130_fd_sc_hd__buf_1','sky130_fd_sc_hd__buf_2','sky130_fd_sc_hd__clkbuf_2','sky130_fd_sc_hd__clkbuf_4'):
            m=db.findMaster(name);print('MASTER',name,m.getWidth(),m.getHeight())
        print('ITERM_ACCESS_API',[n for n in dir(odb.dbITerm) if 'ccess' in n])
        print('INST_ACCESS_API',[n for n in dir(odb.dbInst) if 'ccess' in n])
        if hasattr(odb,'dbWireShapeItr'):print('SHAPE_METHODS',dir(odb.dbWireShapeItr))
(C/'reports/changed_pin_access.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:{'checked':v['checked'],'missing':len(v['missing']),'outside_actual_pin':len(v['outside_actual_pin'])} for k,v in result.items()},indent=2))
