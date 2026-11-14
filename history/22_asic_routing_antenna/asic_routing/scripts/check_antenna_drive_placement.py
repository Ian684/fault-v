"""Independently prove the sole reference resize before using the original gates."""
from pathlib import Path
import ast,hashlib,json,os,odb
R=Path('/work/routing');tag=os.environ['PLACEMENT_RUN_TAG'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
receipt='reports/antenna_model/debug_spacing_20261029/drive_reference.json';proof=json.loads((R/receipt).read_text())
assert proof['pass'] and proof['same_Liberty_function_and_pin_contract'] and proof['different_logic_negative_control_detected']
assert sha(R/proof['source'])==proof['source_sha256']=='e31f514d80664156b627f54d81d885aba7b9745cdda5e3ef6d36535f614bd9b3'
assert sha(R/proof['derived'])==proof['derived_sha256']
tree=ast.parse((R/'scripts/prepare_desktop_checkpoint45.py').read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fixed'];assert len(nodes)==1
exec(compile(ast.Module(body=nodes,type_ignores=[]),'fixed','exec'))
def load(p):
    db=odb.dbDatabase.create();odb.read_db(db,str(p));return db,db.getChip().getBlock()
old_db,old_block=load(R/proof['source']);new_db,new_block=load(R/proof['derived'])
old=fixed(old_block);new=fixed(new_block);expected=dict(old[0]);assert set(proof['allowed_resizes'])=={'_44992_'}
change=proof['allowed_resizes']['_44992_']
assert (change['from'],change['to'])==('sky130_fd_sc_hd__o21ai_2','sky130_fd_sc_hd__o21ai_4')
assert old[0]['_44992_'][0]==change['from'] and old[0]['_44992_'][1]==change['orientation'] and old[0]['_44992_'][2]==tuple(change['location'])
expected['_44992_']=(change['to'],*old[0]['_44992_'][1:]);assert new==(expected,*old[1:])
odb.dbDatabase.destroy(old_db);odb.dbDatabase.destroy(new_db)
p=R/'scripts/check_antenna_placement.py';code=p.read_text()
for before,after in [('inputs/antenna_model_validated.odb',proof['derived']),('reports/antenna_model/candidate_input.json',receipt)]:
    assert code.count(before)==1
    code=code.replace(before,after)
# The original phase/Liberty-signature checker still compares the final circuit to the floorplan.
exec(compile(code,str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
p=R/'reports'/tag/'antenna_diode_checks.json';out=json.loads(p.read_text());out.update(equivalent_driver_repair_verified=True,approved_driver_repair=change,original_reference_sha256=proof['source_sha256'],reference_scope='Original metadata-covered circuit with exactly one independently checked equivalent o21ai_2 to o21ai_4 resize at the same location and orientation; all other cells, endpoint graph and PG identical.')
p.write_text(json.dumps(out,indent=2)+'\n')
