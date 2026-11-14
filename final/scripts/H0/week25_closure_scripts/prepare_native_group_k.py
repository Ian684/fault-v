"""Reconnect only diode branches; prohibit new LI1 outside the diode's physical pin."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_antenna_stubs_f.py').read_text().replace('antenna_stubs_f','native_group_k')
start=code.index("prior=json.loads(");end=code.index('for row,roi in zip(targets,regions):',start)
code=code[:start]+"failed=[];resumed=set()\n"+code[end:]
needle="design.evalTclString('set_thread_count 2')";assert code.count(needle)==1
helpers="""allowed_pin_rects=[]
def inside_diode_pin(q):
    return any(a<=q[0]<=q[2]<=z and c<=q[1]<=q[3]<=f for a,c,z,f in allowed_pin_rects)
@functools.lru_cache(350000)
def wireok(net,l,x1,y1,x2,y2):
    h=width[l]//2;q=[min(x1,x2)-h,min(y1,y2)-h,max(x1,x2)+h,max(y1,y2)+h]
    if l=='li1' and not inside_diode_pin(q):return False
    return clear(net,l,*q)

"""
code=code.replace(needle,helpers+needle)
needle="    return all(clear(net,l,x+a,y+bb,x+c,y+d) for l,a,bb,c,d in data['vias'][vi]['boxes'])";assert code.count(needle)==1
code=code.replace(needle,"    if any(l=='li1' and not inside_diode_pin([x+a,y+bb,x+c,y+d]) for l,a,bb,c,d in data['vias'][vi]['boxes']):return False\n"+needle)
needle="    name=row['net'];net=b.findNet(name);original=primitives(net.getWire())[0]";assert code.count(needle)==1
code=code.replace(needle,needle+"\n    allowed_pin_rects[:]=[rect(q) for l,q in b.findInst(row['diode']).findITerm('DIODE').getGeometries() if l.getName()=='li1'];assert allowed_pin_rects")
needle="        if point not in goals:goals.append(point)";assert code.count(needle)==1
code=code.replace(needle,"        if layer!='li1' and point not in goals:goals.append(point)")
code=code.replace('enumerate(goals[:6])','enumerate(goals[:8])')
needle="            q=('R',layer,x1-5,y1-5,x2+5,y2+5)";assert code.count(needle)==1
code=code.replace(needle,needle+"\n            if layer=='li1' and not inside_diode_pin(q[2:6]):return additions,after")
needle="    if not found:\n        (out/'incomplete.json').write_text(json.dumps({'accepted':accepted,'failed_diode':row['diode'],'accepted_for_final':False},indent=2)+'\\n')\n        raise AssertionError(('No independently clean local diode stub',row['diode']))"
assert code.count(needle)==1
code=code.replace(needle,"    if not found:\n        failed.append(row['diode']);print('DIODE_M1_ACCESS_NOT_FOUND',row['diode'],flush=True)\n    (out/'progress.json').write_text(json.dumps({'accepted':accepted,'failed_diodes':failed,'accepted_for_final':False},indent=2)+'\\n')\nif failed:\n    (out/'incomplete.json').write_text(json.dumps({'accepted':accepted,'failed_diodes':failed,'accepted_for_final':False},indent=2)+'\\n')\n    raise AssertionError(('Some diodes lack a checked inside-pin M1-access branch',failed))")
code=code.replace("'all_original_signal_copper_preserved':True", "'all_original_signal_copper_preserved':True,'new_LI1_restricted_to_actual_diode_LEF_pin':True")
needle="t=Tech();design=Design(t);design.readDb('/runtime_final/antenna_ready.odb')";assert code.count(needle)==1
code=code.replace(needle,"for file,proof in [('/runtime_final/antenna_ready.odb','antenna_access.json'),('/runtime_final/focus_pg.odb','focus_pg_rebase.json')]:\n    with Path(file).open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==json.loads((C/'reports'/proof).read_text())['output_sha256']\n"+needle)
p=C/'scripts/append_native_group_k.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_K_PIN_CONTAINED_LI1_AND_M1_ACCESS_PREPARED')
