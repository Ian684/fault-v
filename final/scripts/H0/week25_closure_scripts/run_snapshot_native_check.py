from pathlib import Path
import hashlib,json,os,shutil,subprocess
C=Path('/work/week25_closure');source=C/'runs/minimal_route_a/1-openroad-detailedrouting/drt_iter13.odb';target=Path('/tmp/snapshot.odb')
with source.open('rb') as inp,target.open('wb') as out:shutil.copyfileobj(inp,out,1024*1024)
with source.open('rb') as inp,target.open('rb') as out:
    original=hashlib.file_digest(inp,'sha256').hexdigest();copied=hashlib.file_digest(out,'sha256').hexdigest()
assert original==copied
(C/'reports/minimal13_copy.json').write_text(json.dumps({'source':str(source),'source_sha256':original,'temporary_runtime_copy_byte_exact':True},indent=2)+'\n')
print('READ_ONLY_SNAPSHOT_COPY_VERIFIED',copied,flush=True)
subprocess.run(['openroad','-exit','-python','/work/routing/scripts/native_route_drc.py'],env=dict(os.environ,ROUTE_DRC_ODB=str(target),ROUTE_DRC_REPORT=str(C/'reports/minimal13_independent_b.json')),check=True)
