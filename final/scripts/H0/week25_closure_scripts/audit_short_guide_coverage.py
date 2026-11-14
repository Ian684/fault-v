"""Check whether the current guides actually cover independently reported shorts."""
from pathlib import Path
import hashlib,json,re,sys
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load,guides
C=Path('/work/week25_closure');p=Path('/runtime/signal_b.odb')
proof=json.loads((C/'reports/short_b_final_independent.json').read_text())
with p.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==proof['odb_sha256']
db,b=load(p);g=guides(b);rows=[]
for m in proof['unresolved']:
    a,c,z,f=m['bbox_dbu'];names=re.findall(r'net:([^\s]+)',m['srcs']);r={'marker':m,'nets':{}}
    for name in names:
        hits=[q for q in g[name] if q[2][0]<=z and q[2][2]>=a and q[2][1]<=f and q[2][3]>=c]
        r['nets'][name]={'guide_count':len(g[name]),'intersecting_guide_layers':[q[0] for q in hits],'matching_layer_guides':sum(q[0]==m['layer'] for q in hits)}
    rows.append(r)
dest=C/'reports/short_b_guide_coverage.json';assert not dest.exists();dest.write_text(json.dumps({'read_only':True,'source_sha256':proof['odb_sha256'],'markers':rows},indent=2)+'\n')
print(json.dumps([{'layer':x['marker']['layer'],'nets':x['nets']} for x in rows],indent=2),flush=True)
