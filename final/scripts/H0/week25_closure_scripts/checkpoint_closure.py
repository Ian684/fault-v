"""Persist current physical evidence without changing frozen W24/W25-front reports."""
from pathlib import Path
from datetime import datetime,timezone
import json,re
C=Path(__file__).resolve().parents[1]
record=json.loads((C/'WORK_STATE.json').read_text())
record.update(updated_utc=datetime.now(timezone.utc).isoformat(),W25_complete=False,foundry_signoff_complete=False,selected_final_candidate=None,status='active_route_density_and_PG_via_repair')
facts=[
 'Dense FOM first full pass: global .390611, 19/1053 windows still below .33 (minimum .317580); all LI/MET1-5 windows pass after LI repair',
 'Native full fill FOM repair removed 3849 dummy islands; LI repair removed only violating whole dummy islands; original circuit geometry unchanged',
 'Identified actual single-cut via4 overcurrent under both 14mW and 28mW/SRAM controlled loads; previous wire-only screen did not cover this',
 'PG trial replaces 183 single-cut contacts; trial A eight-cut arrays reduced IR but created 5 M5 spacing errors; trial B uses 178 eight-cut + 5 four-cut arrays (1444 actual cuts)',
 'Pinned PSM resistor export source audited: CSV current is aggregate per native connection; merged cut count must come from native resistance, not a blanket division by eight',
 'Native WSL temporary inputs are SHA verified copies; durable artifacts and logs remain in E',
]
for item in facts:
    if item not in record['completed']:record['completed'].append(item)
record['in_progress']=[
 '50 equivalent driver full native detailed route: all regular wires rebuilt; not accepted while real DRVs remain',
 'Dense FOM second full experiment uses 0.6um native slot gap; rerun geometry, density and full-chip dummy BEOL checks',
 'PG trial B: fresh native-input IR/EM at 14/28mW per SRAM and complete GDS DRC; requires later application to final 50-driver implementation',
 'Final candidate fresh LVS/antenna/3RC-STA/activity/reset and filled-model coverage review remain pending',
]
for item in ['focus_route_a ended with 312 DRVs','pg_stream_a has 5 M5 spacing violations','dense_fom_native has 19 failing FOM windows','PG native IR c: diagnostic SPICE sink exporter failed map::at; not a complete two-net/case result']:
    if item not in record['not_promoted']:record['not_promoted'].append(item)
text=(C/'logs/full_route.log').read_text(errors='replace')
matches=re.findall(r'Completing \d+% with (\d+) violations',text)
record['route_latest_marker_count']=int(matches[-1]) if matches else None
record['evidence']={'PG_plan':'reports/pg_via_plan_b.json','PG_source':'controls/pinned_psm_source/manifest.json','PG_runs':'scripts/run_pg_native_d.sh','FOM_density_first':'reports/dense_fom_native_density.json','FOM_next':'scripts/run_dense_fom_native_b.sh','FOM_geometry_and_BEOL_next':'scripts/run_dense_b_checks.sh','RCX_negative_control':'reports/fill_rcx_sensitivity.json'}
record['next_action']='Finish native route and trial-B PG DRC/current checks; pass corrected FOM/LI full density and interaction checks; then apply all verified fixes to one candidate and revalidate.'
(C/'WORK_STATE.json').write_text(json.dumps(record,indent=2)+'\n')
r=C.parent/'routing/WORK_STATE.json';data=json.loads(r.read_text(encoding='utf-8-sig'))
data['follow_on_work'].update(state='../week25_closure/WORK_STATE.json',status=record['status'],W25_complete=False,updated_utc=record['updated_utc'],next_action=record['next_action'])
r.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('W25 checkpoint',record['updated_utc'],'latest native router markers',record['route_latest_marker_count'])
