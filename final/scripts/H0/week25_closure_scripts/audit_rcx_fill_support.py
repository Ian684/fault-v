from pathlib import Path
import concurrent.futures,hashlib,json,re,urllib.request
C=Path(__file__).resolve().parents[1]
commit='dcf36133a369abc8f3c5e5738cd4d82e4903c0e0'
repo='The-OpenROAD-Project/OpenROAD'
def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'FaultV-W25-readonly-source-audit'})
    with urllib.request.urlopen(req,timeout=45) as response:return response.read()
tree=json.loads(get(f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1'))
assert not tree.get('truncated')
paths=[entry['path'] for entry in tree['tree'] if entry['type']=='blob' and re.fullmatch(r'src/rcx/(src|include)/.*\.(cpp|h)',entry['path'])]
assert len(paths)>20
folder=C/'controls/pinned_rcx_source';folder.mkdir(parents=True,exist_ok=True)
def save(path):
    data=get(f'https://raw.githubusercontent.com/{repo}/{commit}/{path}')
    destination=folder/path;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
    content=data.decode('utf-8');lines=content.splitlines()
    hits=[{'line':i+1,'text':line.strip()} for i,line in enumerate(lines) if re.search(r'\b(dbFill|getFills|addFill|fill_shape|metal.?fill|floating)\b',line,re.I)]
    return path,{'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'fill_related_hits':hits}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:records=dict(pool.map(save,paths))
result={'repository':repo,'commit':commit,'files':records,'scope':'Read-only pinned-source inventory; absence of text matches is not alone proof that fill is unsupported. Extraction A/B control is required.'}
(C/'reports/RCX_fill_source_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'files':len(records),'bytes':sum(r['bytes'] for r in records.values()),'hits':{p:r['fill_related_hits'] for p,r in records.items() if r['fill_related_hits']}},indent=2))
