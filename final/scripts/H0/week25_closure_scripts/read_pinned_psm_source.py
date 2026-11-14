from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,urllib.request
C=Path(__file__).resolve().parents[1];folder=C/'controls/pinned_psm_source';folder.mkdir(exist_ok=True)
commit='dcf36133a369abc8f3c5e5738cd4d82e4903c0e0'
def get(url):
    request=urllib.request.Request(url,headers={'User-Agent':'FaultV-W25-IR-model-audit'})
    with urllib.request.urlopen(request,timeout=30) as response:return response.read()
items=json.loads(get(f'https://api.github.com/repos/The-OpenROAD-Project/OpenROAD/contents/src/psm/src?ref={commit}'))
files=[i for i in items if i['type']=='file' and i['name'].endswith(('.cpp','.h'))]
def fetch(item):
    name=item['name'];assert Path(name).name==name and '/'+commit+'/' in item['download_url']
    data=get(item['download_url']);(folder/name).write_bytes(data)
    return {'name':name,'url':item['download_url'],'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,files))
(folder/'manifest.json').write_text(json.dumps({'commit':commit,'files':records},indent=2)+'\n')
print('PINNED_PSM_SOURCE',len(records),sum(r['bytes'] for r in records),flush=True)
