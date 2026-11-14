"""Preserve original LI1 components; connect new diode LI1 islands through M1."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_native_group_l.py').read_text().replace('native_group_l','native_group_m')
line="    if l=='li1' and not inside_diode_pin(q):return False\n";assert code.count(line)==1;code=code.replace(line,'')
line="    if any(l=='li1' and not inside_diode_pin([x+a,y+bb,x+c,y+d]) for l,a,bb,c,d in data['vias'][vi]['boxes']):return False\n";assert code.count(line)==1;code=code.replace(line,'')
line="            if layer=='li1' and not inside_diode_pin(q[2:6]):return additions,after\n";assert code.count(line)==1;code=code.replace(line,'')
needle="vs=[{'name':v.getName()";assert code.count(needle)==1
protect="""new_diode_pin_regions=defaultdict(list)
for row in targets:
    new_diode_pin_regions[row['net']].extend(rect(q) for l,q in b.findInst(row['diode']).findITerm('DIODE').getGeometries() if l.getName()=='li1')
for shape in allshapes:
    if shape[0]=='li1' and shape[-1] in new_diode_pin_regions:
        x1,y1,x2,y2=shape[1:5]
        if not any(a<=x1<=x2<=z and c<=y1<=y2<=f for a,c,z,f in new_diode_pin_regions[shape[-1]]):shape[-1]='@protected_original_LI1'
"""
code=code.replace(needle,protect+needle)
needle="    if candidate_via_boxes[vi] in native_vias.get((net,x,y),[]):return True";assert code.count(needle)==1
code=code.replace(needle,"    if data['vias'][vi]['lo']!='li1' and candidate_via_boxes[vi] in native_vias.get((net,x,y),[]):return True")
needle='failed=[];resumed=set()\n';assert code.count(needle)==1
replay="""prior=json.loads((C/'reports/native_group_l/incomplete.json').read_text())['accepted'];assert len(prior)==14
for row in prior:
    assert row['local_native_new_markers']==0 and row['diode'] in access['borrowed_native_accesses']
    assert access['borrowed_native_accesses'][row['diode']]['signal_net']==row['net']
    added=append(b.findNet(row['net']),row['path']);patches=[tuple(q) for q in row['added_primitives'] if q[0]=='R']
    if patches:added+=append_patches(b.findNet(row['net']),patches)
    assert added==Counter(map(tuple,row['added_primitives']))
    accepted.append({**row,'checked_in_previous_trial':'native_group_l'});paths[row['net']].append(row['path']);resumed.add(row['diode'])
    for q in added.elements():add_primitive(q,row['net'])
print('REPLAYED_INSIDE_PIN_M1_BRANCHES',len(resumed),flush=True)
"""
code=code.replace(needle,needle+replay)
code=code.replace("'new_LI1_restricted_to_actual_diode_LEF_pin':True", "'new_LI1_kept_disjoint_from_all_original_signal_LI1':True")
code=code.replace('Only explicit local diode branches added;', 'Only explicit local diode branches added; original signal LI1 shapes are protected even when electrically on the same net;')
p=C/'scripts/append_native_group_m.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_M_PROTECTS_ORIGINAL_LI1_AND_REPLAYS_14_CHECKED_BRANCHES')
