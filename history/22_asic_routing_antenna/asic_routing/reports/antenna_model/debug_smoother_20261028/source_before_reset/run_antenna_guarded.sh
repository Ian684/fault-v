#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?new guarded run tag}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ && ! -e "runs/$tag" && ! -e "../logs/$tag.log" ]]
parent_tag=routed_antenna_residual_20261027_133836
parent="faultv-$parent_tag"
paused=0
finish() {
    result=$?
    trap - EXIT
    docker stop --timeout 5 "faultv-$tag" >/dev/null 2>&1 || true
    restored=0
    if [[ "$paused" == 1 ]] && docker unpause "$parent" >/dev/null 2>&1; then restored=1; fi
    printf '%s\n' "$result" > "../logs/${tag}_followup.exit"
    python3 scripts/antenna_checkpoint_pairs.py "$tag" > "../logs/${tag}_paired_checkpoints.log" 2>&1 || true
    python3 - "$tag" "$result" "$restored" "$parent_tag" <<'PY'
from pathlib import Path
import datetime,json,sys
r=Path('.');tag,result,restored,parent=sys.argv[1:];out=r/'reports'/tag;out.mkdir(parents=True,exist_ok=True)
s=json.loads((r/'accepted_summary.json').read_text());accepted=s['routed_run']==tag and s.get('antenna_closure',False)
record={'run':tag,'pipeline_exit':int(result),'accepted':accepted,'fallback_restored':restored=='1','observed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
p=r.parent/'logs'/f'{tag}.exit'
if p.exists():record['native_exit']=int(p.read_text())
(out/'outcome.json').write_text(json.dumps(record,indent=2)+'\n')
p=r/'WORK_STATE.json';a=json.loads(p.read_text())
if a['active_routed']==tag:
    a['antenna_work']['guarded_trial_result']=record
    if accepted:
        a.update(status='antenna_routing_accepted_delivery_pending',antenna_closure_complete=True,current_live_jobs=[])
        a['antenna_work']['status']='accepted_delivery_pending'
    elif restored=='1':
        a.update(active_routed=parent,status='antenna_residual_repair_running',current_live_jobs=[{'run':parent,'status':'native_running','accepted':False}])
        a['antenna_work'].update(candidate=parent,status='native_residual_repair_running',post_route_antenna_count=None,native_complete_iteration_DRC=[],last_complete_native_DRC=None,last_logged_progress=None)
        for key in ['source_checkpoint_native_DRC','source_checkpoint_antenna_nets','source_checkpoint_sha256','source_checkpoint_iteration','current_input_sha256','latest_iteration','last_complete_iteration','latest_native_marker_types']:
            a['antenna_work'].pop(key,None)
    else:
        a.update(status='antenna_pipeline_stopped',current_live_jobs=[])
        a['antenna_work']['status']='stopped_no_runtime_restore_confirmed'
    a.update(week24_complete=False,ppa_ready=False)
    p.write_text(json.dumps(a,indent=2)+'\n')
PY
    return "$result"
}
trap finish EXIT
python3 scripts/check_inputs.py
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
source_odb=/work/routing/runs/routed_antenna_bounded_20261028_110309/1-openroad-detailedrouting/antenna_connected.odb
docker run --rm --user 1000:1000 --memory=2200m -e "ANTENNA_AUDIT_ODB=$source_odb" -e "ANTENNA_AUDIT_REPORT=/work/routing/reports/antenna_model/${tag}_coverage.json" -v "$root:/work" -w /work/routing "$image" openroad -exit -python scripts/audit_antenna_metadata.py > "$root/logs/${tag}_input_coverage.log" 2>&1
python3 - "$tag" <<'PY'
from pathlib import Path
import datetime,hashlib,json,sys
r=Path('.');tag=sys.argv[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proof='reports/antenna_model/debug_review_20261028_0352/bounded_connected.json';a=json.loads((r/proof).read_text());source=r/a['source']
assert a['source_odb_sha256']==sha(source)=='d71ed45e51889a3147458984b502bfce4a46a6db0182199e99b0ce0d3ff7d50c' and a['native_antenna_violating_nets']==0
report=source.parent/'antenna_connection.drc-6.rpt';assert report.read_text().count('violation type:')==110
coverage=f'reports/antenna_model/{tag}_coverage.json';cov=json.loads((r/coverage).read_text());assert cov['pass'] and not cov['missing_active_input_models'] and cov['source_odb_sha256']==sha(source)
conn='reports/antenna_model/routed_antenna_focus_20261028_120458_source_connectivity.json';physical=json.loads((r/conn).read_text());assert physical['pass'] and physical['source_odb_sha256']==sha(source) and physical['unconnected_diode_terminals']==0
s=json.loads((r/'antenna_bounded_state.json').read_text());s['odb']='/work/routing/'+a['source']
(r/'antenna_guarded_state.json').write_text(json.dumps(s,indent=2)+'\n')
c=json.loads((r/'config_routed_antenna_bounded_20261028_110309.json').read_text());assert c['CLOCK_PERIOD']==40 and c['DRT_OPT_ITERS']==64 and c['ERROR_ON_TR_DRC'] is True
c.update(DRT_THREADS=4,DRT_ANTENNA_REPAIR_ITERS=0)
(r/f'config_{tag}.json').write_text(json.dumps(c,indent=2)+'\n')
files=['scripts/antenna_guarded_cli.py','scripts/drt_antenna_guarded.tcl','scripts/run_antenna_guarded.sh','scripts/antenna_checkpoint_pairs.py','scripts/accept_antenna_guarded_phase.py','scripts/accept_antenna_phase.py',f'config_{tag}.json','antenna_guarded_state.json',proof,conn,coverage,'reports/antenna_model/sram_antenna_model.json','macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef']
launch={'accepted':False,'run':tag,'cli':files[0],'config':f'config_{tag}.json','state':'antenna_guarded_state.json','distribution':'Ubuntu-D','threads':4,'memory_mb':6500,'budget_seconds':1800,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':{n:sha(r/n) for n in files},'input_sha256':sha(source),'source_native_DRC':110,'source_antenna_nets':0,'scope':'Ordinary ROUTED zero-antenna source, four short native repair stages, committed ODB/hash/antenna pair after every stage, abort on antenna regression or two stages without a new best. All final acceptance gates unchanged.'}
(r/'reports'/f'{tag}_launch.json').write_text(json.dumps(launch,indent=2)+'\n')
PY
[[ "$(docker inspect -f '{{.State.Running}} {{.State.Paused}}' "$parent")" == 'true false' ]]
docker pause "$parent" >/dev/null;paused=1
set +e
timeout --signal=TERM --kill-after=10 1800 docker run --rm --name "faultv-$tag" --user 1000:1000 --memory=6500m --memory-swap=6500m --cpus=4 -v "$root:/work" -w /work/routing "$image" python3 scripts/antenna_guarded_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/antenna_guarded_state.json --run-tag "$tag" "config_${tag}.json" > "$root/logs/$tag.log" 2>&1
result=$?
printf '%s\n' "$result" > "$root/logs/$tag.exit"
python3 - "$tag" "$result" <<'PY'
from pathlib import Path
import json,sys
p=Path('reports')/(sys.argv[1]+'_launch.json');a=json.loads(p.read_text());a['native_exit']=int(sys.argv[2]);p.write_text(json.dumps(a,indent=2)+'\n')
PY
[[ "$result" == 0 ]] || exit "$result"
set -e
bash scripts/run_antenna_checks.sh "$tag"
python3 scripts/accept_antenna_guarded_phase.py "$tag"
docker stop --timeout 5 "$parent" >/dev/null
paused=0
