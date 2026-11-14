from pathlib import Path
import json,hashlib,datetime
R=Path('/work/routing');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
script=R/'scripts/prepare_clock_rules.py';frozen=json.loads((R/'input_identity.json').read_text(encoding='utf-8'))['sha256'];assert sha(script)==frozen['scripts/prepare_clock_rules.py']
audit=R/'reports/clock_routing_rules.json';record=json.loads(audit.read_text(encoding='utf-8'));src=R/'inputs/fault_v_asic_top.odb';target=R/'inputs/standard_clock_rules.odb';assert not target.exists() and sha(src)==record['source_sha256']
report_sha=sha(audit);state_sha=sha(R/'initial_state.json');text=script.read_text(encoding='utf-8');assert text.count('report={')==1
# Execute only the frozen source loader and the original exact 13-NDR removal/write.
namespace={'__file__':str(script)};exec(compile(text.split('report={',1)[0],str(script),'exec'),namespace)
assert sha(target)==record['derived_sha256'],'Reconstructed historical input must exactly match its original SHA-256'
assert sha(audit)==report_sha and sha(R/'initial_state.json')==state_sha and sha(src)==record['source_sha256']
receipt={'pass':True,'source':str(src.relative_to(R)),'source_sha256':sha(src),'restored':str(target.relative_to(R)),'restored_sha256':sha(target),'original_expected_sha256':record['derived_sha256'],'generator':'scripts/prepare_clock_rules.py','generator_sha256':sha(script),'restored_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Recover the missing historical standard-clock routing input with the frozen original generator. Restored ODB matches its original recorded SHA-256 exactly. Original source, clock-rules receipt and initial_state.json are unchanged. Final accepted design is untouched.'};(R/'reports/desktop_restore_clock_rules.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt,indent=2),flush=True)
