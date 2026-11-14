from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_native_group_r.py').read_text().split("design.evalTclString('set_thread_count 2')")[0].replace('native_group_r','native_group_s')
code=code.replace("in ('li1','met1')]", "in ('li1','met1','met2','met3')]")
code+='''
rows=[]
for row,roi in zip(targets,regions):
    pins=[rect(q) for l,q in b.findInst(row['diode']).findITerm('DIODE').getGeometries() if l.getName()=='li1']
    rows.append({'target':row,'roi':roi,'pins':pins,'old_branch':old_branches[row['diode']]})
(out/'access_geometry.json').write_text(json.dumps({'rows':rows,'shapes':allshapes,'vias':vs,'spacing':spacing,'width':width})+'\\n')
print('PIN_ACCESS_GEOMETRY_EXPORTED',len(rows),len(allshapes),flush=True)
'''
p=C/'scripts/diagnose_pin_access_s.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,newline='\n')
print('S_DIAGNOSTIC_READY')
