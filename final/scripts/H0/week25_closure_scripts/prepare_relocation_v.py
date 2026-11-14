from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_native_group_u.py').read_text().replace('native_group_u','native_group_v')
helper='''def cell_geometry(inst):
    result=[]
    for pin in inst.getITerms():
        for layer,q in pin.getGeometries():result.append([layer.getName(),*rect(q),pin.getNet().getName() if pin.getNet() else '@pin'])
    orient=str(inst.getOrient());ox,oy=inst.getLocation();mw=inst.getMaster().getWidth();mh=inst.getMaster().getHeight()
    assert orient in ('R0','MX','MY','R180')
    for q in inst.getMaster().getObstructions():
        x1,y1,x2,y2=rect(q)
        if orient in ('MY','R180'):x1,x2=mw-x2,mw-x1
        if orient in ('MX','R180'):y1,y2=mh-y2,mh-y1
        result.append([q.getTechLayer().getName(),ox+x1,oy+y1,ox+x2,oy+y2,'@obs'])
    return result

'''
needle='accepted=[];paths=defaultdict(list);failed=[];relocations=[]';assert code.count(needle)==1;code=code.replace(needle,helper+needle)
old="""        for pin in diode.getITerms():
            for layer,q in pin.getGeometries():shapes.append([layer.getName(),*rect(q),pin.getNet().getName() if pin.getNet() else '@pin'])
        assert not list(diode.getMaster().getObstructions()),'Diode OBS require transformed addition'
"""
assert code.count(old)==1;code=code.replace(old,"        shapes.extend(cell_geometry(diode))\n")
old="""            for pin in diode.getITerms():
                for layer,q in pin.getGeometries():add(layer.getName(),rect(q),pin.getNet().getName() if pin.getNet() else '@pin')
"""
assert code.count(old)==1;code=code.replace(old,"            for shape in cell_geometry(diode):add(shape[0],shape[1:5],shape[-1])\n")
p=C/'scripts/append_native_group_v.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,newline='\n')
sh=(C/'scripts/run_native_group_u.sh').read_text().replace('native_group_u','native_group_v').replace('native-group-u','native-group-v').replace('antenna_native_u','antenna_native_v')
(C/'scripts/run_native_group_v.sh').write_text(sh,newline='\n');print('V_TRANSFORMED_DIODE_OBS_INCLUDED')
