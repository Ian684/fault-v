"""Windows-side byte stream avoids large reads through the WSL 9P mount."""
from pathlib import Path
import hashlib,json,subprocess,time
C=Path(__file__).resolve().parents[1]
root='/tmp/faultv-w25-closure-20261030'
prefix=['wsl','-d','Ubuntu-D','--exec']
subprocess.run(prefix+['mkdir','-p',root],check=True)
items=[('F.odb',C.parent/'week25_front/runs/fill_only_20261029_a/1-openroad-fillinsertion/fault_v_asic_top.odb'),('A13.odb',C/'runs/minimal_route_a/1-openroad-detailedrouting/drt_iter13.odb'),('cached_guided.odb',C/'inputs/cached_guided.odb'),('fault_v_asic_top.gds',C/'runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds')]
mags=sorted((C/'dense_fom_full_development').glob('fault_v_asic_top_fill_pattern_*_*.mag'));assert len(mags)==20
items += [(p.name,p) for p in mags]
record={'runtime_root':root,'durable_data_remains_in_E':True,'started_unix':time.time(),'files':{}}
for name,source in items:
    with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    destination=root+'/'+name
    exists=subprocess.run(prefix+['test','-e',destination]).returncode==0
    if not exists:
        with source.open('rb') as f:subprocess.run(prefix+['tee',destination+'.part'],stdin=f,stdout=subprocess.DEVNULL,check=True)
        copied=subprocess.check_output(prefix+['sha256sum',destination+'.part'],text=True).split()[0]
        assert copied==digest,(name,copied,digest)
        subprocess.run(prefix+['mv',destination+'.part',destination],check=True)
    else:
        assert subprocess.check_output(prefix+['sha256sum',destination],text=True).split()[0]==digest,name
    record['files'][name]={'original':str(source),'bytes':source.stat().st_size,'sha256':digest}
    (C/'reports/native_runtime_stage.json').write_text(json.dumps(record,indent=2)+'\n')
    print('NATIVE_RUNTIME_VERIFIED',name,source.stat().st_size,flush=True)
record['completed_unix']=time.time();(C/'reports/native_runtime_stage.json').write_text(json.dumps(record,indent=2)+'\n')
