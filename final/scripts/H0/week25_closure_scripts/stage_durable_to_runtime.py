"""Copy one durable E-backed artifact to a new native alias, preserving exact bytes."""
from pathlib import Path
import hashlib,json,re,shutil,sys
C=Path('/work/week25_closure');source=Path(sys.argv[1]).resolve();name=sys.argv[2]
assert source.is_relative_to(C) and source.is_file() and re.fullmatch(r'[a-z0-9_]+\.(?:odb|gds|vcd)',name)
root=Path('/runtime');dest=root/name;assert dest.resolve().parent==root
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
digest=sha(source)
if not dest.exists():
    part=dest.with_name(dest.name+'.part');assert not part.exists()
    with source.open('rb') as f,part.open('xb') as o:shutil.copyfileobj(f,o,1024*1024)
    assert sha(part)==digest;part.rename(dest)
assert sha(dest)==sha(source)==digest
record={'source':str(source),'runtime':'/var/tmp/faultv-w25-closure-20261101/'+name,'bytes':source.stat().st_size,'sha256':digest,'durable_output_in_E':True,'method':'Native copy from durable E-backed artifact; existing aliases may only contain the same SHA256.'}
p=C/'reports'/('runtime_'+name.replace('.','_')+'.json')
if p.exists():assert json.loads(p.read_text())['sha256']==digest
else:p.write_text(json.dumps(record,indent=2)+'\n')
print('DURABLE_RUNTIME_ALIAS_VERIFIED',name,digest,flush=True)
