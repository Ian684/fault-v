"""The original macro model must be rejected by the same native coverage audit."""
from pathlib import Path
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]
old=R/'runs/routed_desktop_residual_four_20261026_174504/final/odb/fault_v_asic_top.odb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(old)=='196e8c9b7d74a0000d8b0869b9b6d2cc9ad7a73b7b44b6a3f389ce25d758cc16'
rejected=R/'reports/antenna_model/negative_must_not_accept.json'
assert not rejected.exists()
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
cmd=['docker','run','--rm','--user','1000:1000','--memory=2200m','-e','ANTENNA_AUDIT_ODB=/work/routing/'+old.relative_to(R).as_posix(),'-e','ANTENNA_AUDIT_REPORT=/work/routing/'+rejected.relative_to(R).as_posix(),'-v',str(R.parent)+':/work','-w','/work/routing',image,'openroad','-exit','-python','scripts/audit_antenna_metadata.py']
p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(R/'reports/antenna_model/negative_coverage.log').write_text(p.stdout)
assert p.returncode==1 and 'Missing macro gate model' in p.stdout and not rejected.exists(),p.stdout
receipt={'pass':True,'known_incomplete_source_sha256':sha(old),'checker_sha256':sha(R/'scripts/audit_antenna_metadata.py'),'expected_exit':1,'actual_exit':p.returncode,'reason':'Missing macro gate model','no_acceptance_report_created':True,'image':image}
(R/'reports/antenna_model/negative_coverage.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
