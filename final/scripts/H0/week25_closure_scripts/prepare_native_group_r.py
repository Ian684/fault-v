from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/append_native_group_l.py').read_text().replace('native_group_l','native_group_r')
code=code.replace("('/runtime_final/antenna_ready.odb','antenna_access.json')", "('/runtime_final/native_group_p.odb','native_group_p/result.json')").replace("design.readDb('/runtime_final/antenna_ready.odb')", "design.readDb('/runtime_final/native_group_p.odb')")
code=code.replace('obstructions,primitives\n','obstructions,primitives,encode_fixed\n',1)
needle="targets=json.loads((C/'reports/antenna_stub_full_targets.json').read_text())['diodes']";assert code.count(needle)==1
extra="""mproof=json.loads((C/'reports/native_group_m/result.json').read_text());failed_before=set(json.loads((C/'reports/native_group_l/incomplete.json').read_text())['failed_diodes']);bad_nets={'_16390_','net3327','net4749','net660','net7318'}
old_branches={r['diode']:r for r in mproof['accepted'] if r['diode'] in failed_before and r['net'] in bad_nets};assert len(old_branches)==5
targets=[r for r in targets if r['diode'] in old_branches];assert len(targets)==5
text=(R/'scripts/search_manual_eco.py').read_text();tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='normalize_routes'];assert len(nodes)==1;exec(compile(ast.Module(body=nodes,type_ignores=[]),'normalizer','exec'))
"""
code=code.replace(needle,needle+'\n'+extra)
start=code.index("for name in access['cleared_signal_nets']:");end=code.index('original_wires=wires(b)',start)+len('original_wires=wires(b)')
replacement="""original_wires=wires(b);base_geometry={}
for row in targets:
    n=b.findNet(row['net']);g=primitives(n.getWire())[0];removed=Counter(map(tuple,old_branches[row['diode']]['added_primitives']));assert not removed-g
    base=g-removed;encode_fixed(n.getWire(),base,tech,b);normalize_routes(n.getWire());assert primitives(n.getWire())[0]==base;base_geometry[row['net']]=base
"""
code=code[:start]+replacement+code[end:]
code=code.replace("if v.getBottomLayer().getName() in ('li1','met1','met2','met3','met4')", "if v.getBottomLayer().getName() in ('li1','met1')")
needle="design.evalTclString('set_thread_count 2')";assert code.count(needle)==1
code=code.replace(needle,"from pin_access_search import make_pin_access_search\nsearch=make_pin_access_search(globals())\n"+needle)
needle="    for trial,end in enumerate(goals[:8]):";assert code.count(needle)==1
code=code.replace(needle,"    old_end=tuple(old_branches[row['diode']]['path'][-1]['to']);assert old_end[2] in (1,2)\n    goals=[old_end]+[q for q in goals if q!=old_end and q[2] in (1,2)]\n"+needle)
start=code.index('        odb.dbWire.destroy(net.getWire());netwire=');end=code.index('        assert primitives(net.getWire())[0]==original',start)+len('        assert primitives(net.getWire())[0]==original')
code=code[:start]+"        encode_fixed(net.getWire(),original,tech,b);normalize_routes(net.getWire());assert primitives(net.getWire())[0]==original"+code[end:]
code=code.replace('assert len(accepted)==20','assert len(accepted)==5')
code=code.replace("assert primitives(b.findNet(name).getWire())[0]==primitives(rb.findNet(name).getWire())[0]+additions", "assert primitives(b.findNet(name).getWire())[0]==base_geometry[name]+additions")
code=code.replace("'diodes_connected_with_checked_stubs':len(accepted)", "'rerouted_diode_branches':len(accepted),'passive_diodes_added':20")
code=code.replace("'all_original_signal_copper_preserved':True", "'all_P_source_copper_except_five_replaced_branches_preserved':True,'pin_access_method':'5nm mcon centre enumeration inside the unchanged diode pin; M1/M2 search only'")
p=C/'scripts/append_native_group_r.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('R_FINE_IN_PIN_MCON_ACCESS_PREPARED_FOR_FIVE_BRANCHES')
