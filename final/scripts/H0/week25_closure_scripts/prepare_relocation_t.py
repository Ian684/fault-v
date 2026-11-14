from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_native_group_r.py').read_text().replace('native_group_r','native_group_t')
code=code.replace("regions.append([min(p[0] for p in xy)-6000,min(p[1] for p in xy)-6000,max(p[0] for p in xy)+6000,max(p[1] for p in xy)+6000])", "regions.append([min(p[0] for p in xy)-25000,min(p[1] for p in xy)-25000,max(p[0] for p in xy)+25000,max(p[1] for p in xy)+25000])")
needle='for i in b.getInsts():\n    if not any';assert code.count(needle)==1
code=code.replace(needle,"relocating={'ANTENNA_7559','ANTENNA_7560','ANTENNA_7567','ANTENNA_7572'}\nfor i in b.getInsts():\n    if i.getName() in relocating:continue\n    if not any")
start=code.index('accepted=[];paths=defaultdict(list)');end=code.index('if failed:\n',start)
code=code[:start]+'''
accepted=[];paths=defaultdict(list);failed=[];relocations=[]
prior=json.loads((C/'reports/native_group_r/incomplete.json').read_text())['accepted'];assert len(prior)==1
for row in prior:
    n=b.findNet(row['net']);added=append(n,row['path']);patches=[tuple(q) for q in row['added_primitives'] if q[0]=='R']
    if patches:added+=append_patches(n,patches)
    assert added==Counter(map(tuple,row['added_primitives']))
    accepted.append({**row,'replayed_checked_inside_pin_branch':'native_group_r'});paths[row['net']].append(row['path'])
    for q in added.elements():add_primitive(q,row['net'])
print('REPLAYED_R_INSIDE_PIN_BRANCH',flush=True)
for row,roi in zip(targets,regions):
    if row['diode'] not in relocating:continue
    diode=b.findInst(row['diode']);name=row['net'];net=b.findNet(name);original=primitives(net.getWire())[0]
    old=tuple(diode.getLocation());orient=str(diode.getOrient());w=diode.getMaster().getWidth();h=diode.getMaster().getHeight();own=list(diode.findITerm('DIODE').getPrefAccessPoints());assert own
    px,py=own[0].getPoint();goal=tuple(old_branches[row['diode']]['path'][-1]['to']);assert goal[2] in (1,2)
    boxes=[rect(i.getBBox()) for i in b.getInsts() if i.getName()!=diode.getName()]
    occupied=defaultdict(list)
    for a,c,z,f in boxes:
        if a>roi[2] or z<roi[0] or c>roi[3] or f<roi[1]:continue
        for y in range(c//2720,f//2720+1):occupied[y].append((a,c,z,f))
    candidates=[]
    for rr in b.getRows():
        q=rect(rr.getBBox());y=q[1]
        if str(rr.getOrient())!=orient or abs(y+py-goal[1])>15000 or (y-old[1])%340:continue
        x0=q[0]+round((goal[0]-px-q[0])/460)*460
        near={tuple(v) for yy in range(y//2720,(y+h)//2720+1) for v in occupied[yy]}
        for offset in range(-32,33):
            x=x0+offset*460
            if x<max(q[0],roi[0]+2000) or x+w>min(q[2],roi[2]-2000) or y<roi[1]+2000 or y+h>roi[3]-2000 or (x-old[0])%460:continue
            if any(x<a2 and x+w>a1 and y<b2 and y+h>b1 for a1,b1,a2,b2 in near):continue
            distance=abs(x+px-goal[0])+abs(y+py-goal[1]);candidates.append((distance,x,y))
    candidates=sorted(set(candidates));print('FREE_SAME_PHASE_PLACEMENTS',row['diode'],len(candidates),'cells',len(boxes),flush=True)
    found=False;attempts=[]
    for index,(distance,x,y) in enumerate(candidates[:80]):
        diode.setLocation(x,y)
        allowed_pin_rects[:]=[rect(q) for l,q in diode.findITerm('DIODE').getGeometries() if l.getName()=='li1'];assert allowed_pin_rects
        data['region']=roi;shapes=[q for q in allshapes if intersects(q[1:5],roi)]
        for pin in diode.getITerms():
            for layer,q in pin.getGeometries():shapes.append([layer.getName(),*rect(q),pin.getNet().getName() if pin.getNet() else '@pin'])
        assert not list(diode.getMaster().getObstructions()),'Diode OBS require transformed addition'
        rebuild();start=(x+px,y+py,0);path=search(name,start,goal)
        if path is None:attempts.append({'location':[x,y],'legal_path':False});continue
        path=compact(path);added=append(net,path);assert primitives(net.getWire())[0]==original+added
        after=check(row['diode']+f'_placement{index}',roi)
        if not after:
            paths[name].append(path);accepted.append({'diode':row['diode'],'net':name,'path':path,'added_primitives':list(added.elements()),'local_native_new_markers':0,'placement_trial':index})
            relocations.append({'diode':row['diode'],'master':diode.getMaster().getName(),'net':name,'old_location':list(old),'new_location':[x,y],'orientation':orient,'same_phase_and_empty_native_row_slot':True,'local_native_DRC':0,'attempts':attempts})
            for q in added.elements():add_primitive(q,name)
            for pin in diode.getITerms():
                for layer,q in pin.getGeometries():add(layer.getName(),rect(q),pin.getNet().getName() if pin.getNet() else '@pin')
            found=True;print('RELOCATED_AND_CONNECTED',row['diode'],old,(x,y),len(path),flush=True);break
        attempts.append({'location':[x,y],'local_native_markers':sum(after.values())})
        encode_fixed(net.getWire(),original,tech,b);normalize_routes(net.getWire());assert primitives(net.getWire())[0]==original
    if not found:
        diode.setLocation(*old);failed.append(row['diode']);print('NO_ACCEPTED_RELOCATION',row['diode'],flush=True)
    (out/'progress.json').write_text(json.dumps({'accepted':accepted,'relocations':relocations,'failed_diodes':failed,'accepted_for_final':False},indent=2)+'\\n')
''' + code[end:]
needle='assert len(accepted)==5 and fixed(b)==before and guides(b)==oldg and obstructions(b)==oldo';assert code.count(needle)==1
code=code.replace(needle,'''assert len(accepted)==5 and len(relocations)==4 and guides(b)==oldg and obstructions(b)==oldo
expected=dict(before[0])
for row in relocations:
    old=expected[row['diode']];assert list(old[1])==row['old_location'];expected[row['diode']]=(old[0],tuple(row['new_location']),*old[2:])
assert fixed(b)==(expected,before[1],before[2]),'Only the four reviewed added passive diode locations may change'
response=str(design.evalTclString('set e [catch {check_placement -verbose} msg]; list $e $msg'));assert response.startswith('0 '),response
''')
code=code.replace("'all_cells_graph_PG_guides_obstructions_unchanged':True", "'all_original_cells_graph_PG_guides_obstructions_unchanged':True,'only_added_passive_diode_locations_changed':relocations,'placement_response':response")
p=C/'scripts/append_native_group_t.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,newline='\n')
print('T_RELOCATION_PREPARED')
