"""Seal final W25 evidence and independently re-read all bytes before status promotion."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
C=Path(__file__).resolve().parents[1];A=C.parent;mode=sys.argv[1];assert mode in ('create','verify')
manifest=C/'W25_Evidence_Manifest.json'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
result=read(C/'reports/W25_closure_result.json');assert result['W25_complete'] and result['all_requested_research_core_gates_pass'] and not result['foundry_signoff_complete']
for stem,digest in result['gate_report_sha256'].items():assert sha(C/'reports'/(stem+'.json'))==digest
assert sha(C/'W25_Closure_Report.md')==result['report_sha256']
for name,digest in result['frozen_review_sha256'].items():assert sha(A/name)==digest
tags=['antenna_native_w','focus_post_b','focus_post_sta_b','final_core_lvs_a','final_ir_0p014_a','final_ir_0p028_a']
for tag in tags:assert (C/'logs'/(tag+'.exit')).read_text().strip()=='0'
for job in ('final_post_b','final_core_lvs','final_stream_audits','final_functional','final_ir','final_fill'):
    assert (C/'logs'/(job+'.exit')).read_text().strip()=='0'
if mode=='create':
    assert not manifest.exists();paths=set()
    for folder in ('scripts','controls','macros','reports'):
        paths.update(p for p in (C/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for tag in tags:paths.update(p for p in (C/'runs'/tag).rglob('*') if p.is_file())
    paths.update(p for p in (C/'functional/final_a').rglob('*') if p.is_file())
    paths.update(p for p in (C/'final_fill').rglob('*') if p.is_file())
    paths.update(p for p in C.iterdir() if p.is_file() and (p.suffix=='.json' or p.name in ('W25_Closure_Report.md','Reproduce_W25.md')) and p.name!='WORK_STATE.json')
    paths.update(C/'logs'/(tag+'.exit') for tag in tags)
    paths.update(C/'logs'/(job+'.exit') for job in ('final_post_b','final_core_lvs','final_stream_audits','final_functional','final_ir','final_fill'))
    paths.update(C/'inputs'/name for name in ('native_group_w.odb','antenna_ready.odb','final_core_lvs.gds','final_badpin_lvs.gds'))
    paths.update(A/name for name in result['frozen_review_sha256'])
    def referenced_files(value):
        if isinstance(value,dict):
            for k,v in value.items():yield from referenced_files(k);yield from referenced_files(v)
        elif isinstance(value,list):
            for v in value:yield from referenced_files(v)
        elif isinstance(value,str) and value.startswith('/work/'):
            p=A/Path(value).relative_to('/work')
            assert p.resolve().is_relative_to(A.resolve()),value
            if p.is_file():yield p
    for tag in tags:paths.update(referenced_files(read(C/'runs'/tag/'resolved.json')))
    paths.update(referenced_files(read(C/'functional/final_a/result.json')))
    paths.add(A/'routing/sta_tool/sta')
    paths.update(p for p in (A/'routing/scripts').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    records={}
    for i,p in enumerate(sorted(paths)):
        assert p.resolve().is_relative_to(A.resolve()) and not p.is_symlink(),str(p)
        records[p.relative_to(A).as_posix()]={'bytes':p.stat().st_size,'sha256':sha(p)}
        if i%100==0:print('W25_SEAL_PROGRESS',i,len(paths),flush=True)
    record={'created_utc':datetime.now(timezone.utc).isoformat(),'scope':'W25 final research core evidence; rejected diagnostic reports retained explicitly, never promoted by manifest membership','root':'fault-v-asic','files':records,'file_count':len(records),'bytes':sum(r['bytes'] for r in records.values()),'result_sha256':sha(C/'reports/W25_closure_result.json')}
    manifest.write_text(json.dumps(record,indent=2)+'\n');print('W25_MANIFEST_CREATED',len(records),record['bytes'],flush=True)
else:
    record=read(manifest);assert record['file_count']==len(record['files']) and record['result_sha256']==sha(C/'reports/W25_closure_result.json')
    total=0
    for i,(name,row) in enumerate(record['files'].items()):
        p=A/name;assert p.resolve().is_relative_to(A.resolve()) and not p.is_symlink() and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],name
        total+=row['bytes']
        if i%100==0:print('W25_VERIFY_PROGRESS',i,len(record['files']),flush=True)
    assert total==record['bytes'];print('W25_ALL_SEALED_EVIDENCE_FRESHLY_VERIFIED',len(record['files']),total,sha(manifest),flush=True)
