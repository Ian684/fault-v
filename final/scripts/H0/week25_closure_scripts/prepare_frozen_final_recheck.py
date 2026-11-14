from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/verify_frozen_evidence.py').read_text().replace('prior_evidence_integrity_20261101.json','frozen_final_recheck_20261101.json')
needle="result={}\n";assert code.count(needle)==1
code=code.replace(needle,"assert not (C/'reports/frozen_final_recheck_20261101.json').exists()\n"+needle)
p=C/'scripts/verify_frozen_evidence_final.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code,newline='\n')
print('FROZEN_FINAL_RECEIPT_NEW_PATH_READY')
