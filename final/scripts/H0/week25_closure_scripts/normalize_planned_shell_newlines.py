"""Normalize inactive planned W25 shell launchers to LF; preserve before/after hashes."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1];names=['run_native_group_i.sh','run_final_fill_parallel.sh','run_final_post_b.sh','run_final_core_lvs.sh','run_final_stream_audits.sh','run_final_functional.sh','run_final_ir.sh','run_final_fill.sh','run_final_candidate_c.sh','run_native_candidate_checks.sh'];rows=[]
for name in names:
    p=C/'scripts'/name;old=p.read_bytes();new=old.replace(b'\r\n',b'\n')
    if name=='run_native_group_i.sh':new=new.replace(b'native-group-h',b'native-group-i')
    assert b'\r' not in new
    if new!=old:p.write_bytes(new)
    rows.append({'file':name,'old_sha256':hashlib.sha256(old).hexdigest(),'new_sha256':hashlib.sha256(new).hexdigest(),'CRLF_lines_before':old.count(b'\r\n'),'LF_verified':True})
p=C/'reports/planned_shell_LF_20261101.json';assert not p.exists();p.write_text(json.dumps(rows,indent=2)+'\n')
print('PLANNED_SHELL_LF_VERIFIED',[(r['file'],r['CRLF_lines_before']) for r in rows])
