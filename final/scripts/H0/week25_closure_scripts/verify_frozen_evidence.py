"""Verify all frozen stages while writing the new receipt only in closure evidence."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
result={}
for name in ('signoff_precheck','week25_front','week25_signoff','ppa'):
    folder=C.parent/name
    manifest=next(p for p in (folder/'work_manifest.json',folder/'review_manifest.json') if p.exists())
    records=json.loads(manifest.read_text(encoding='utf-8-sig'))['sha256'];assert records
    for relative,expected in records.items():
        path=folder/relative;assert path.is_file() and sha(path)==expected,(name,relative)
    result[name]={'manifest_sha256':sha(manifest),'files_verified':len(records),'all_unchanged':True}
out=C/'reports/prior_evidence_integrity_20261101.json';assert not out.exists()
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2),flush=True)
