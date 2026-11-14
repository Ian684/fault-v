"""Point the final gates at the corrected post-B case, preserving the A recipes."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1];backup=C/'controls/pre_post_b_scripts';backup.mkdir(exist_ok=False)
names=['prepare_final_core_lvs.py','run_final_core_lvs.sh','run_final_stream_audits.sh','run_final_functional.sh','prepare_final_ir.py']
records={}
for name in names:
    p=C/'scripts'/name;old=p.read_text();assert 'focus_post_a' in old
    (backup/name).write_bytes(p.read_bytes());new=old.replace('focus_post_a','focus_post_b')
    if p.suffix=='.py':compile(new,str(p),'exec')
    p.write_text(new)
    records[name]={'before_sha256':hashlib.sha256(old.encode()).hexdigest(),'after_sha256':hashlib.sha256(new.encode()).hexdigest(),'preserved_copy':(backup/name).relative_to(C).as_posix()}
(C/'reports/final_helpers_post_b_binding.json').write_text(json.dumps({'post_tag':'focus_post_b','changes':records},indent=2)+'\n')
print('FINAL_HELPERS_BOUND_TO_POST_B',len(records),flush=True)
