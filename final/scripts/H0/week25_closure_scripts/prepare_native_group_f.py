"""Preserve all good initial routing and expand only measured local escape guides."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/route_native_group_e.py').read_text().replace('native_group_e','native_group_f').replace('-or_seed 43 -or_k 7','-or_seed 47 -or_k 7')
needle="out=C/'reports/native_group_f';out.mkdir(exist_ok=False);protected=[]"
assert code.count(needle)==1
insert="""added_guides=[]
for name in sorted(dirty):
    n=b.findNet(name)
    for layer in ('met1','met2','met3','met4','met5'):
        l=tech.findLayer(layer);box=[1568000,622000,1615000,669000]
        g=odb.dbGuide_create(n,l,l,odb.Rect(*box),False);assert g
        g.setIsConnectedToTerm(False);g.setIsJumper(False)
        added_guides.append({'net':name,'layer':layer,'bbox_dbu':box})
oldg=guides(b)
"""
code=code.replace(needle,insert+needle)
needle="    if n.getName() in dirty:\n        odb.dbWire.destroy(n.getWire());continue"
assert code.count(needle)==1;code=code.replace(needle,"    if n.getName() in dirty:continue")
code=code.replace("'protected_routes':len(protected),'accepted_for_final':False", "'protected_routes':len(protected),'all_initial_routes_retained':True,'added_local_escape_guides':added_guides,'accepted_for_final':False")
code=code.replace("'editable_nets':sorted(dirty),'protected_routes':len(protected),'protected_wire_bytes_exactly_restored'", "'editable_nets':sorted(dirty),'all_initial_routes_retained':True,'added_local_escape_guides':added_guides,'protected_routes':len(protected),'protected_wire_bytes_exactly_restored'")
p=C/'scripts/route_native_group_f.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_F_RETAINS_ALL_INITIAL_ROUTES_WITH_LOCAL_ESCAPE_GUIDES')
