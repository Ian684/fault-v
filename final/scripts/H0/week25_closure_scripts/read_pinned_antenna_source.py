"""Preserve the exact standalone detailed-route antenna repair implementation."""
from pathlib import Path
import hashlib,json,urllib.request
C=Path(__file__).resolve().parents[1]
commit='dcf36133a369abc8f3c5e5738cd4d82e4903c0e0'
dest=C/'controls/pinned_antenna_source';dest.mkdir(exist_ok=True)
records=[]
for name in ('GlobalRouter.tcl','GlobalRouter.cpp','RepairAntennas.cpp'):
    url=f'https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD/{commit}/src/grt/src/{name}'
    with urllib.request.urlopen(url,timeout=30) as response:raw=response.read()
    target=dest/name
    if target.exists():assert target.read_bytes()==raw
    else:target.write_bytes(raw)
    records.append({'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
tcl=(dest/'GlobalRouter.tcl').read_text();cpp=(dest/'GlobalRouter.cpp').read_text()
assert '[grt::have_routes] || [grt::have_detailed_routes]' in tcl and '-diode_only' in tcl
assert 'haveDetailedRoutes()' in cpp and 'initFastRoute(min_layer, max_layer)' in cpp
(C/'reports/native_antenna_source.json').write_text(json.dumps({'commit':commit,'files':records,'standalone_detailed_route_entry_supported':True,'scope':'API/source audit only; actual insertion, placement, original-object invariants and final antenna/connectivity checks remain mandatory.'},indent=2)+'\n')
print('PINNED_DETAILED_ROUTE_ANTENNA_ENTRY_VERIFIED')
