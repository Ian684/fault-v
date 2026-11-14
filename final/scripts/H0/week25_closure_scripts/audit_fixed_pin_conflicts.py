"""Separate unmovable LEF pin conflicts from ordinary signal-route shorts."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load
C=Path('/work/week25_closure');source=Path('/runtime/focus14.odb')
raw=json.loads((C/'reports/focus14_raw.json').read_text())
with source.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==raw['source_sha256']
db,b=load(source);u=b.getDbUnitsPerMicron();cache={}
def hits(a,z):return a[0]<=z[2] and a[2]>=z[0] and a[1]<=z[3] and a[3]>=z[1]
assert hits((0,0,10,10),(10,0,20,10)) and not hits((0,0,10,10),(11,0,20,10))
def pins(netname,layer):
    key=netname,layer
    if key not in cache:
        net=b.findNet(netname);assert net,netname;rows=[]
        for term in net.getITerms():
            for tech,z in term.getGeometries():
                if tech.getName()==layer:rows.append({'inst':term.getInst().getName(),'pin':term.getMTerm().getName(),'box':[z.xMin(),z.yMin(),z.xMax(),z.yMax()]})
        cache[key]=rows
    return cache[key]
results=[];counts=Counter();fixed=[]
for marker in raw['markers']:
    if marker['type']!='Short':continue
    nets=list(dict.fromkeys(re.findall(r'net:([^\s]+)',marker['srcs'])))
    if len(nets)!=2:counts['other_source_count']+=1;continue
    box=[round(v*u) for v in marker['bbox_um']]
    a=[p for p in pins(nets[0],marker['layer']) if hits(p['box'],box)]
    z=[p for p in pins(nets[1],marker['layer']) if hits(p['box'],box)]
    pairs=[{'first':p,'second':q} for p in a for q in z if hits(p['box'],q['box'])]
    kind='fixed_pin_pair_overlap' if pairs else 'route_to_pin' if a or z else 'route_to_route'
    counts[kind]+=1;row={**marker,'classification':kind,'pins_first':a,'pins_second':z,'overlapping_pin_pairs':pairs};results.append(row)
    if pairs:fixed.append(row)
record={'source_sha256':raw['source_sha256'],'short_classifications':dict(counts),'fixed_pin_conflicts':fixed,'shorts':results,'scope':'LEF pin-rectangle abstraction on a fixed completed checkpoint. A pin-pair overlap is a fixed routing-model conflict, not automatically a manufacturing-GDS defect. Zero such overlaps rules out this specific placement hypothesis; routing and pin/obstruction checks still apply.'}
(C/'reports/focus14_pin_conflicts.json').write_text(json.dumps(record,indent=2)+'\n')
print('FIXED_PIN_AUDIT',dict(counts),flush=True)
