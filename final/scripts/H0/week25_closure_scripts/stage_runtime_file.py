"""Stage one E-drive artifact to native WSL storage with end-to-end SHA verification."""
from pathlib import Path
import hashlib,json,subprocess,sys
C=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]).resolve();name=sys.argv[2]
assert source.is_relative_to(C.parent) and source.is_file()
assert name==Path(name).name and '/' not in name and '\\' not in name
root='/var/tmp/faultv-w25-closure-20261101'
dest=root+'/'+name;prefix=['wsl','-d','Ubuntu-D','--exec']
subprocess.run(prefix+['mkdir','-p',root],check=True)
with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
if subprocess.run(prefix+['test','-e',dest]).returncode:
    with source.open('rb') as f:subprocess.run(prefix+['tee',dest+'.part'],stdin=f,stdout=subprocess.DEVNULL,check=True)
    assert subprocess.check_output(prefix+['sha256sum',dest+'.part'],text=True).split()[0]==digest
    subprocess.run(prefix+['mv',dest+'.part',dest],check=True)
else:assert subprocess.check_output(prefix+['sha256sum',dest],text=True).split()[0]==digest
record={'source':str(source),'runtime':dest,'bytes':source.stat().st_size,'sha256':digest,'durable_output_in_E':True}
(C/'reports'/('runtime_'+name.replace('.','_')+'.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
