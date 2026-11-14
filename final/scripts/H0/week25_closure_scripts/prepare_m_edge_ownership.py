from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/analyze_m_li1_components.py').read_text().replace('rows=[]','rows=[];components=[]',1)
needle="    if wn or near_rule:rows.append({'bbox_dbu':bounds,'wire_owners':wn,'pin_names':sorted({p[2]+'/'+p[3] for p in pins}),'pin_net_owners':sorted({p[0] for p in pins}),'crosses_CE_near_violation':near_rule,'outside_CE_area_um2':(r-ce).area()*l.dbu*l.dbu})"
assert code.count(needle)==1
code=code.replace(needle,"    info={'bbox_dbu':bounds,'wire_owners':wn,'pin_names':sorted({p[2]+'/'+p[3] for p in pins}),'pin_net_owners':sorted({p[0] for p in pins})};components.append((r,info))")
code=code[:code.index('masters={}')]+'''import re,xml.etree.ElementTree as ET
root=ET.parse(C/'runs/native_m_stream_a/3-klayout-drc/reports/drc.klayout.lyrdb').getroot();edges=[]
for item in root.findall('items/item'):
    assert item.findtext('category').strip("'")=='li.3'
    for value in item.findall('values/value'):
        q=[round(float(x)*1000) for x in re.findall(r'-?\\d+(?:\\.\\d+)?',value.text or '')];assert len(q)==8
        owners=[];ids=[]
        for offset in (0,4):
            x=(q[offset]+q[offset+2])//2;y=(q[offset+1]+q[offset+3])//2;point=pya.Region(pya.Box(x-3,y-3,x+3,y+3))
            found=[(i,info) for i,(r,info) in enumerate(components) if not r.interacting(point).is_empty()];ids.append({i for i,info in found});owners.append([info for i,info in found])
        edges.append({'edge_pair_dbu':q,'same_component':bool(ids[0]&ids[1]),'owners':owners})
assert len(edges)==23
record={'source_GDS_sha256':data['source_GDS_sha256'],'same_component_notches':sum(v['same_component'] for v in edges),'different_component_spacing':sum(not v['same_component'] for v in edges),'edge_pairs':edges}
out=C/'reports/m_li1_edge_ownership.json';assert not out.exists();out.write_text(json.dumps(record,indent=2)+'\\n')
print('ACTUAL_LI1_EDGE_OWNERSHIP',record['same_component_notches'],record['different_component_spacing'],flush=True)
for e in edges:print(e['same_component'],[[(i['wire_owners'],i['pin_names']) for i in side] for side in e['owners']],e['edge_pair_dbu'],flush=True)
'''
p=C/'scripts/analyze_m_edge_ownership.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('M_ACTUAL_RULE_EDGE_OWNERSHIP_PREPARED')
