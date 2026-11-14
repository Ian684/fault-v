from pathlib import Path
from collections import Counter
import hashlib,json,xml.etree.ElementTree as ET
C=Path(__file__).resolve().parents[1]
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert (C/'logs/li1_rule_replay.exit').read_text().strip()=='0'
plan=json.loads((C/'reports/li1_closure_plan.json').read_text())
simulated=C/Path(plan['simulated_GDS']).relative_to('/work/week25_closure')
assert sha(simulated)==plan['simulated_GDS_sha256']
counts=[]
for stem in ('li1_baseline_replay','li1_fixed_replay'):
    root=ET.parse(C/'reports'/(stem+'.rdb')).getroot();assert root.tag=='report-database' and len(root.findall('categories/category'))==2
    counts.append(Counter(i.findtext('category').strip("'") for i in root.findall('items/item')))
assert counts[0]=={'li.3':43} and not counts[1]
record={'source_GDS_sha256':plan['source_GDS_sha256'],'simulated_GDS_sha256':plan['simulated_GDS_sha256'],'original_li3_markers':43,'fixed_li1_and_li3_markers':0,'patches':len(plan['patches']),'rule_replay_sha256':sha(C/'controls/li3_replay.drc'),'scope':'Exact pinned public LI1 width/spacing expressions replayed as a diagnostic. Full process deck and actual core LVS are still mandatory.'}
(C/'reports/li1_rule_replay_verified.json').write_text(json.dumps(record,indent=2)+'\n');print('ACTUAL_LI1_RULE_REPLAY_PASS_43_TO_0',flush=True)
