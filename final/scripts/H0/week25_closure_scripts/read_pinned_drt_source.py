from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,urllib.request
C=Path(__file__).resolve().parents[1];folder=C/'controls/pinned_drt_source';folder.mkdir(exist_ok=True)
commit='dcf36133a369abc8f3c5e5738cd4d82e4903c0e0'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'FaultV-W25-local-source-audit'})
    with urllib.request.urlopen(req,timeout=30) as response:return response.read()
url=f'https://api.github.com/repos/The-OpenROAD-Project/OpenROAD/contents/src/drt/src/io?ref={commit}'
items=json.loads(get(url));assert isinstance(items,list)
files=[i for i in items if i['type']=='file' and i['name'].endswith(('.cpp','.h'))]
def fetch(item):
    assert '/'+commit+'/' in item['download_url']
    data=get(item['download_url']);(folder/item['name']).write_bytes(data)
    return {'name':item['name'],'url':item['download_url'],'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,files))
(folder/'manifest.json').write_text(json.dumps({'commit':commit,'files':records},indent=2)+'\n')
print('PINNED_DRT_IO_SOURCE',len(records),[i['name'] for i in records],flush=True)
