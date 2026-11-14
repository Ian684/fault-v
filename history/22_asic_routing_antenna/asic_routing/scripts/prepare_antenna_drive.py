"""Resize the sole measured electrical violator; reroute only its four incident nets."""
from pathlib import Path
from openroad import Tech,Design
import ast,hashlib,json,re,struct,odb
R=Path('/work/routing');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'runs/routed_antenna_spacing_20261029_1700/final/odb/fault_v_asic_top.odb'
assert sha(source)=='d113d8ebb2c911b719dcac65cfb361bc927086af99998b82ad251866ce433b5d'
pair=json.loads((source.parents[2]/'1-openroad-detailedrouting/intervention_pair.json').read_text())
assert pair['native_DRC']==pair['antenna_nets']==0 and pair['odb_sha256']==sha(source)
for file,names in [('prepare_desktop_checkpoint45.py',{'fixed'}),('prepare_cold_corner_reguide.py',{'wires','guides','guide_sig','obstructions'})]:
    tree=ast.parse((R/'scripts'/file).read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names];assert {n.name for n in nodes}==names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),file,'exec'))
lib=R.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib'
text=lib.read_text()
def logic(name):
    start=text.index('cell ("'+name+'")');end=text.find('\n    cell (',start+10);cell=text[start:end if end>=0 else len(text)]
    pins=list(re.finditer(r'(?<![\w_])pin\s*\("([^"]+)"\)\s*\{',cell));sig={}
    for k,p in enumerate(pins):
        body=cell[p.end():pins[k+1].start() if k+1<len(pins) else len(cell)]
        direction=re.search(r'\bdirection\s*:\s*"?(input|output|inout)"?',body);function=re.search(r'\bfunction\s*:\s*"([^"]+)"',body)
        if direction:sig[p[1]]=(direction[1],re.sub(r'\s+','',function[1]) if function else None)
    return sig,tuple(re.findall(r'\b(clock(ed)?_on|next_state|clear|preset)\s*:\s*"([^"]+)"',cell))
old='sky130_fd_sc_hd__o21ai_2';new='sky130_fd_sc_hd__o21ai_4'
assert logic(old)==logic(new) and logic(old)!=logic('sky130_fd_sc_hd__nor2_2')
t=Tech();t.readLiberty(str(lib));t.readLiberty(str(R/'macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib'))
design=Design(t);design.readDb(str(source));d=design.getDb();b=d.getChip().getBlock()
before=fixed(b);before_wires=wires(b);before_guides=guides(b);before_obs=obstructions(b)
i=b.findInst('_44992_');assert i and i.getMaster().getName()==old
location=tuple(i.getLocation());orient=str(i.getOrient());assert location==(2384640,2265760) and orient=='MX'
affected={term.getNet().getName() for term in i.getITerms() if str(term.getMTerm().getSigType()) not in ['POWER','GROUND']}
assert affected=={'_16274_','_16304_','_16310_','_16311_'}
assert i.swapMaster(d.findMaster(new));i.setLocation(*location)
def placement():
    v=str(design.evalTclString('set drive_status [catch {check_placement -verbose} drive_result]; list $drive_status [string is integer -strict $drive_result] $drive_result')).split()
    return len(v)>=2 and v[0]=='0' and (v[1]=='0' or len(v)==3 and v[2]=='0')
assert placement(),'Larger driver does not fit existing placement'
i.setLocation(2383260,2265760);assert not placement(),'Native placement missed deliberate overlap';i.setLocation(*location)
after=fixed(b);expected=dict(before[0]);expected['_44992_']=(new,*before[0]['_44992_'][1:])
assert after==(expected,*before[1:]) and obstructions(b)==before_obs and guides(b)==before_guides and wires(b)==before_wires
for name in affected:
    net=b.findNet(name);assert net.getWire();odb.dbWire.destroy(net.getWire())
retained={n:h for n,h in before_wires.items() if n not in affected};assert len(retained)==41333 and wires(b)==retained
partial=R/'inputs/antenna_drive_partial.odb';global_input=R/'inputs/antenna_drive_global.odb'
assert not partial.exists() and not global_input.exists();odb.write_db(d,str(partial))
for net in b.getNets():
    if net.getWire():odb.dbWire.destroy(net.getWire())
assert not wires(b) and fixed(b)==after and obstructions(b)==before_obs
odb.write_db(d,str(global_input))
base=R/'inputs/antenna_model_validated.odb';assert sha(base)=='e31f514d80664156b627f54d81d885aba7b9745cdda5e3ef6d36535f614bd9b3'
rd=odb.dbDatabase.create();odb.read_db(rd,str(base));rb=rd.getChip().getBlock();ref_before=fixed(rb);ri=rb.findInst('_44992_')
assert ri.getMaster().getName()==old and tuple(ri.getLocation())==location and str(ri.getOrient())==orient
assert ri.swapMaster(rd.findMaster(new));ri.setLocation(*location)
ref_expected=dict(ref_before[0]);ref_expected['_44992_']=(new,*ref_before[0]['_44992_'][1:]);assert fixed(rb)==(ref_expected,*ref_before[1:])
reference=R/'inputs/antenna_drive_reference.odb';assert not reference.exists();odb.write_db(rd,str(reference))
folder=R/'reports/antenna_model/debug_spacing_20261029'
ref_record={'pass':True,'source':base.relative_to(R).as_posix(),'source_sha256':sha(base),'derived':reference.relative_to(R).as_posix(),'derived_sha256':sha(reference),'allowed_resizes':{'_44992_':{'from':old,'to':new,'location':location,'orientation':orient}},'Liberty_sha256':sha(lib),'same_Liberty_function_and_pin_contract':True,'different_logic_negative_control_detected':True,'all_other_cells_graph_PG_unchanged':True}
(folder/'drive_reference.json').write_text(json.dumps(ref_record,indent=2)+'\n')
state={'odb':'/work/routing/inputs/antenna_drive_global.odb','metrics':{}}
for key in ['nl','pnl','sdc','json_h','vh']:
    paths=list((source.parents[1]/key).glob('*'));assert len(paths)==1
    state[key]='/work/routing/'+paths[0].relative_to(R).as_posix()
(R/'antenna_drive_global_state.json').write_text(json.dumps(state,indent=2)+'\n')
c=json.loads((R/'config_antenna_4319_control_global.json').read_text());assert c['CLOCK_PERIOD']==40 and not c['GRT_ALLOW_CONGESTION']
(R/'config_antenna_drive_global.json').write_text(json.dumps(c,indent=2)+'\n')
a={'pass':True,'accepted':False,'source':source.relative_to(R).as_posix(),'source_sha256':sha(source),'partial':partial.relative_to(R).as_posix(),'partial_sha256':sha(partial),'global_input':global_input.relative_to(R).as_posix(),'global_input_sha256':sha(global_input),'resized_instance':'_44992_','old_master':old,'new_master':new,'location':location,'orientation':orient,'cleared_whole_nets':sorted(affected),'retained_exact_wires':41333,'Liberty_sha256':sha(lib),'same_Liberty_function_and_pin_contract':True,'placement_overlap_negative_control_detected':True,'all_other_cells_graph_PG_obstructions_unchanged':True,'reference_receipt':(folder/'drive_reference.json').relative_to(R).as_posix(),'scope':'Exactly one equivalent drive-size change at unchanged location/orientation, with legal footprint. Four incident signal nets require native pin access, matching new zero-overflow guides, rerouting, antenna, independent DRC and extracted-RC/TT validation. Constraints unchanged.'}
(folder/'drive_input.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a,indent=2),flush=True)
