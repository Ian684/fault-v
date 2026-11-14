"""Copy a completed native run to its canonical E-drive path, verifying every file."""
from pathlib import Path
import hashlib,json,shutil,sys
source=Path('/native_run');target=Path(sys.argv[1])
assert target.parent==Path('/work/week25_closure/runs') and target.name==sys.argv[2]
assert source.is_dir() and (not target.exists() or not any(target.iterdir()))
target.mkdir(exist_ok=True);records={}
for p in sorted(source.rglob('*')):
    assert not p.is_symlink(),p
    if not p.is_file():continue
    rel=p.relative_to(source);dest=target/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    with p.open('rb') as inp,dest.open('xb') as out:shutil.copyfileobj(inp,out,1024*1024)
    def sha(q):
        with q.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    digest=sha(p);assert sha(dest)==digest,rel
    records[rel.as_posix()]={'bytes':p.stat().st_size,'sha256':digest}
assert records,'No native outputs to archive'
(target/'native_archive_manifest.json').write_text(json.dumps({'files':records,'all_byte_exact':True,'canonical_paths_preserved':True},indent=2)+'\n')
print('NATIVE_RUN_ARCHIVED',target,len(records),flush=True)
