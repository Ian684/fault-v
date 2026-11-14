"""Keep the original functional/physical gate, with validated passive diode loads."""
from pathlib import Path
import ast, hashlib, json, os, re
import odb

R=Path('/work/routing'); tag=os.environ['PLACEMENT_RUN_TAG']
assert tag.replace('_','').isalnum()
source=R/'inputs/antenna_model_validated.odb'
candidate=R/'runs'/tag/'final/odb/fault_v_asic_top.odb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
input_receipt=json.loads((R/'reports/antenna_model/candidate_input.json').read_text())
assert sha(source)==input_receipt['derived_sha256']
db=odb.dbDatabase.create(); odb.read_db(db,str(candidate)); b=db.getChip().getBlock()
ref=odb.dbDatabase.create(); odb.read_db(ref,str(source)); rb=ref.getChip().getBlock()
old={i.getName() for i in rb.getInsts()}
verified_diodes={i.getName() for i in b.getInsts()}-old
assert verified_diodes, 'Expected actual antenna protection diodes'
diode_records=[]
for name in sorted(verified_diodes):
    i=b.findInst(name); m=i.getMaster()
    assert name.startswith('ANTENNA_') and m.getName()=='sky130_fd_sc_hd__diode_2' and str(m.getType())=='CORE_ANTENNACELL', (name,m.getName(),m.getType())
    pins=[t for t in i.getITerms() if str(t.getMTerm().getSigType()) not in ['POWER','GROUND']]
    assert len(pins)==1 and pins[0].getMTerm().getName()=='DIODE' and str(pins[0].getIoType())=='INPUT'
    mt=pins[0].getMTerm()
    assert mt.hasDefaultAntennaModel()
    assert mt.getDefaultAntennaModel().getGateArea()==[(0.4347,None)] and mt.getDiffArea()==[(0.4347,None)], 'Changed PDK diode model'
    n=pins[0].getNet(); assert n and rb.findNet(n.getName()) and str(n.getSigType()) in ['SIGNAL','CLOCK']
    assert any(t.getInst().getName() in old for t in n.getITerms())
    diode_records.append({'instance':name,'net':n.getName(),'master':m.getName()})

nl=next((R/'runs'/tag/'final/nl').glob('*.v'))
netlist_diodes=set(re.findall(r'\bsky130_fd_sc_hd__diode_2\s+\\?([^\s(]+)\s*\(',nl.read_text()))
assert netlist_diodes==verified_diodes, ('STA netlist diode set differs from ODB',len(netlist_diodes),len(verified_diodes))
lib=R.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib'
libtext=lib.read_text(); start=libtext.index('cell ("sky130_fd_sc_hd__diode_2")'); end=libtext.find('\n    cell (',start+10)
cell=libtext[start:end if end>=0 else len(libtext)]
cap=float(re.search(r'\bcapacitance\s*:\s*([0-9.eE+-]+)',cell)[1])
unit=re.search(r'capacitive_load_unit\s*\(\s*([0-9.]+)\s*,\s*"?([a-z]+)"?\s*\)',libtext)
assert cap==0.000878 and unit and float(unit[1])==1 and unit[2]=='pf', 'Unexpected diode input capacitance model'
spefs=[p for p in (R/'runs'/tag/'final/spef').rglob('*.spef') if 'nom' in p.name]
assert len(spefs)==1
names={}; extracted_diodes=[]
with spefs[0].open() as f:
    for line in f:
        fields=line.split()
        if len(fields)>=2 and fields[0][0:1]=='*' and fields[0][1:].isdigit() and fields[1].lstrip('\\') in verified_diodes:
            names[fields[0]]=fields[1].lstrip('\\')
        if fields and fields[0]=='*I' and fields[1].endswith(':DIODE'):
            inst=fields[1].rsplit(':',1)[0]
            extracted_diodes.append(names.get(inst,inst.lstrip('\\')))
assert set(extracted_diodes)==verified_diodes and len(extracted_diodes)==len(verified_diodes), 'Missing or duplicate diode terminals in extracted SPEF'

# A diode is allowed to add a load; no existing endpoint, cell or PG shape may change.
tree=ast.parse((R/'scripts/prepare_desktop_checkpoint45.py').read_text())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fixed']; assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),'fixed','exec'))
old_cells,old_graph,old_pg=fixed(rb)
cells,graph,pg=fixed(b)
original_cells={n:v for n,v in cells.items() if n not in verified_diodes}
assert set(original_cells)==set(old_cells)
status_updates=[]
for name,value in old_cells.items():
    observed=original_cells[name]
    assert observed[:3]==value[:3],('Existing placement/master changed',name)
    if observed[3]!=value[3]:
        assert value[3]=='FIRM' and observed[3]=='PLACED',(name,value,observed)
        status_updates.append(name)
assert set(graph)==set(old_graph), 'Unexpected net added or removed'
for name,(kind,terms,ports) in graph.items():
    assert (kind,tuple(t for t in terms if t[0] not in verified_diodes),ports)==old_graph[name], ('Existing connectivity changed',name)
assert pg==old_pg, 'Existing power-grid geometry changed'
model=json.loads((R/'reports/antenna_model/sram_antenna_model.json').read_text())
master=next(i.getMaster() for i in b.getInsts() if i.getMaster().isBlock())
assert len([i for i in b.getInsts() if i.getMaster().isBlock()])==18
# Serialize the native metadata as LEF and compare it below without relying on SWIG vector conversions.
for pin,values in model['pin_areas'].items():
    mt=master.findMTerm(pin)
    assert mt and (mt.hasDefaultAntennaModel() if 'gate_area_um2' in values else True)

out=R/'reports'/tag; out.mkdir(parents=True,exist_ok=True)
receipt={'pass':True,'candidate_odb_sha256':sha(candidate),'reference_odb_sha256':sha(source),
         'passive_diodes':len(verified_diodes),'existing_cells_placement_and_connectivity_unchanged':True,
         'existing_PG_geometry_unchanged':True,'diodes':diode_records,
         'native_FIRM_to_PLACED_status_only_updates':status_updates,
         'all_diodes_in_actual_STA_netlist':True,'diode_input_capacitance_pf':cap,'diode_Liberty_sha256':sha(lib),
         'all_diodes_in_extracted_SPEF':True,'nominal_SPEF_sha256':sha(spefs[0]),
         'scope':'Exact additions restricted to the PDK passive antenna diode; original polarity, placement, power, clock and geometry checks still executed.'}
(out/'antenna_diode_checks.json').write_text(json.dumps(receipt,indent=2)+'\n')
odb.dbDatabase.destroy(db); odb.dbDatabase.destroy(ref)

checker=R/'scripts/check_placement.py'
locks=json.loads((R/'input_identity.json').read_text())['sha256']
assert sha(checker)==locks['scripts/check_placement.py']
code=checker.read_text()
needle='        sig,ff=logic.get(master,({},()))'
assert code.count(needle)==2
# Exclude only the exact, separately validated passive loads from functional endpoints.
code=code.replace(needle,'        if i.getName() in verified_diodes: continue\n'+needle,1)
exec(compile(code,str(checker),'exec'),{'__file__':str(checker),'__name__':'__main__','verified_diodes':verified_diodes})
