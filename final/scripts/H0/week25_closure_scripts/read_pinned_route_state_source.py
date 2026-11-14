"""Read the exact running router's route-reuse implementation before changing strategy."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,urllib.request
C=Path(__file__).resolve().parents[1];dest=C/'controls/pinned_route_state_source';dest.mkdir(exist_ok=True)
commit='dcf36133a369abc8f3c5e5738cd4d82e4903c0e0'
files=['src/drt/src/TritonRoute.cpp','src/drt/src/dr/FlexDR.cpp','src/drt/src/dr/FlexDR_init.cpp','src/drt/src/dr/FlexDR_end.cpp']
def fetch(path):
    url=f'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/{commit}/{path}'
    with urllib.request.urlopen(url,timeout=30) as response:raw=response.read()
    target=dest/Path(path).name
    if target.exists():assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    return {'path':path,'url':url,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,files))
(dest/'manifest.json').write_text(json.dumps({'commit':commit,'files':records},indent=2)+'\n')
print('PINNED_ROUTE_STATE_SOURCE',len(records),sum(r['bytes'] for r in records))
