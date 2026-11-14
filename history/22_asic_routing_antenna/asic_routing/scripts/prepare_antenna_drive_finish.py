from pathlib import Path
import hashlib,json,shutil
R=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=R/'runs/routed_antenna_drive_20261029_171855/1-openroad-detailedrouting/intervention_final.odb'
digest='4ee109b70cf46419e228db7fd1641b3be5aed8460da1796eb5348dac294affc0';assert sha(source)==digest
pair=json.loads(source.with_name('intervention_pair.json').read_text());assert pair['native_DRC']==0 and pair['antenna_nets']==2 and pair['odb_sha256']==digest
target=R/'inputs/antenna_drive_finish_source.odb';assert not target.exists();shutil.copyfile(source,target);assert sha(target)==digest
state=json.loads((R/'antenna_drive_state.json').read_text());state['odb']='/work/routing/inputs/antenna_drive_finish_source.odb'
(R/'antenna_drive_finish_state.json').write_text(json.dumps(state,indent=2)+'\n')
c=json.loads((R/'config_routed_antenna_drive_20261029_171855.json').read_text());c.update(DRT_ANTENNA_REPAIR_ITERS=4,DRT_ANTENNA_REPAIR_MARGIN=0,DRT_THREADS=8)
assert c['CLOCK_PERIOD']==40 and c['ERROR_ON_TR_DRC'] and c['DRT_OPT_ITERS']==64
(R/'config_antenna_drive_finish.json').write_text(json.dumps(c,indent=2)+'\n')
a={'pass':True,'accepted':False,'source':source.relative_to(R).as_posix(),'source_sha256':digest,'derived':target.relative_to(R).as_posix(),'derived_sha256':digest,'source_native_DRC':0,'source_antenna_nets':2,'source_receipt':'reports/antenna_model/debug_spacing_20261029/drive_input.json','continuation_stage':'two_antenna_nets_after_driver_reroute','source_passive_diodes':7551,'scope':'Exact coherent DRC-zero source after one equivalent driver resize. Repair only actual antenna violators using unchanged native rules, then reroute/extract and require every original physical/electrical gate.'}
(R/'reports/antenna_model/debug_spacing_20261029/drive_finish_input.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps(a,indent=2))
