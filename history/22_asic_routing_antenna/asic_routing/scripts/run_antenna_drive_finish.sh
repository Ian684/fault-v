#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?new antenna finish tag}"
global_tag="${2:?final-placement global proof tag}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ && "$global_tag" =~ ^[A-Za-z0-9_]+$ && ! -e "runs/$tag" && ! -e "runs/$global_tag" ]]
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
parent=faultv-routed_antenna_checkpoint_20261029_151959
finish() {
    result=$?;trap - EXIT
    docker stop --timeout 5 "faultv-$tag" >/dev/null 2>&1 || true
    docker stop --timeout 5 "faultv-$global_tag" >/dev/null 2>&1 || true
    if [[ "$result" != 0 ]]; then docker unpause "$parent" >/dev/null 2>&1 || true; fi
    printf '%s\n' "$result" > "../logs/${tag}_followup.exit"
    return "$result"
}
trap finish EXIT
python3 scripts/check_inputs.py
[[ "$(docker inspect -f '{{.State.Running}} {{.State.Paused}}' "$parent")" == 'true true' ]]
python3 - "$tag" <<'PY'
from pathlib import Path
import datetime,hashlib,json,sys
r=Path('.');tag=sys.argv[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();folder='reports/antenna_model/debug_spacing_20261029'
receipt=f'{folder}/drive_finish_input.json';a=json.loads((r/receipt).read_text());assert a['pass'] and a['source_native_DRC']==0 and a['source_antenna_nets']==2 and sha(r/a['derived'])==a['derived_sha256']
prior=json.loads((r/'reports/routed_antenna_drive_20261029_171855_launch.json').read_text())
for n,h in prior['sha256'].items():assert sha(r/n)==h,n
c=json.loads((r/'config_antenna_drive_finish.json').read_text());assert c['CLOCK_PERIOD']==40 and c['ERROR_ON_TR_DRC'] and c['DRT_OPT_ITERS']==64 and c['DRT_ANTENNA_REPAIR_ITERS']==4 and c['DRT_ANTENNA_REPAIR_MARGIN']==0
(r/f'config_{tag}.json').write_text(json.dumps(c,indent=2)+'\n')
files=set(prior['sha256'])|{'scripts/antenna_drive_finish_cli.py','scripts/drt_antenna_closure.tcl','scripts/run_antenna_drive_finish.sh','scripts/prepare_antenna_drive_finish.py','scripts/final_antenna_global_proof.py','scripts/accept_antenna_drive_finish_phase.py','antenna_drive_finish_state.json',f'config_{tag}.json',receipt,a['derived'],a['source'],'reports/antenna_model/debug_spacing_20261029/drive2_antenna.json'}
launch={'accepted':False,'run':tag,'global_run':prior['global_run'],'routing_input_global_run':prior['global_run'],'cli':'scripts/antenna_drive_finish_cli.py','state':'antenna_drive_finish_state.json','config':f'config_{tag}.json','placement_checker':'scripts/check_antenna_drive_placement.py','distribution':'Ubuntu-D','threads':8,'memory_mb':6500,'input_sha256':a['derived_sha256'],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':{n:sha(r/n) for n in sorted(files)},'scope':'Continue coherent DRC0/antenna2 driver repair. Native diode-only repair targets actual violations with unchanged antenna rules; final RC/TT, full DRC and exact-final-placement global proof required.'}
(r/'reports'/f'{tag}_launch.json').write_text(json.dumps(launch,indent=2)+'\n')
p=r/'WORK_STATE.json';s=json.loads(p.read_text());s.update(active_routed=tag,status='antenna_driver_finish',week24_complete=False,antenna_closure_complete=False,ppa_ready=False,current_live_jobs=[{'run':tag,'distribution':'Ubuntu-D','status':'native_running','accepted':False},{'run':'routed_antenna_checkpoint_20261029_151959','status':'paused_preserved','accepted':False},{'run':'routed_antenna_residual_20261027_133836','status':'paused_preserved','accepted':False}]);s['antenna_work'].update(candidate=tag,status='driver_repair_two_antenna_nets',current_stage='native_two_net_antenna_finish',finish_input_receipt=receipt);p.write_text(json.dumps(s,indent=2)+'\n')
PY
set +e
docker run --rm --name "faultv-$tag" --user 1000:1000 --memory=6500m --memory-swap=6500m --cpus=8 -v "$root:/work" -w /work/routing "$image" python3 scripts/antenna_drive_finish_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/antenna_drive_finish_state.json --run-tag "$tag" "config_${tag}.json" > "$root/logs/$tag.log" 2>&1
result=$?;printf '%s\n' "$result" > "$root/logs/$tag.exit"
python3 - "$tag" "$result" <<'PY'
from pathlib import Path
import json,sys
p=Path('reports')/(sys.argv[1]+'_launch.json');a=json.loads(p.read_text());a['native_exit']=int(sys.argv[2]);p.write_text(json.dumps(a,indent=2)+'\n')
PY
[[ "$result" == 0 ]] || exit "$result"
set -e
docker run --rm --user 1000:1000 --memory=2600m --cpus=1 -v "$root:/work" -w /work/routing "$image" openroad -exit -python scripts/final_antenna_global_proof.py "$tag" "$global_tag" prepare > "$root/logs/${global_tag}_prepare.log" 2>&1
python3 - "$global_tag" <<'PY'
from pathlib import Path
import datetime,hashlib,json,sys
r=Path('.');g=sys.argv[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();a=json.loads((r/'reports'/f'{g}_input.json').read_text());assert a['pass']
files=['scripts/final_antenna_global_proof.py','scripts/antenna_corridor_global_cli.py','scripts/grt_antenna_corridor.tcl','scripts/check_global.py',f'{g}_state.json',f'config_{g}.json',f'reports/{g}_input.json',a['input']]
(r/'reports'/f'{g}_launch.json').write_text(json.dumps({'accepted':False,'run':g,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'input_sha256':a['input_sha256'],'input':a['input'],'config':f'config_{g}.json','state':f'{g}_state.json','sha256':{n:sha(r/n) for n in files},'scope':'Native global capacity proof using all final cells/diodes, unchanged endpoint graph, PG and restrictions.'},indent=2)+'\n')
PY
set +e
timeout --signal=TERM --kill-after=10 600 docker run --rm --name "faultv-$global_tag" --user 1000:1000 --memory=3000m --cpus=2 -v "$root:/work" -w /work/routing "$image" python3 scripts/antenna_corridor_global_cli.py --pdk-root /work/pdk --with-initial-state "/work/routing/${global_tag}_state.json" --run-tag "$global_tag" "config_${global_tag}.json" > "$root/logs/$global_tag.log" 2>&1
result=$?;printf '%s\n' "$result" > "$root/logs/$global_tag.exit"
[[ "$result" == 0 ]] || exit "$result"
set -e
python3 scripts/check_global.py "$global_tag"
docker run --rm --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/routing "$image" openroad -exit -python scripts/final_antenna_global_proof.py "$tag" "$global_tag" verify > "$root/logs/${global_tag}_verify.log" 2>&1
python3 - "$tag" "$global_tag" <<'PY'
from pathlib import Path
import hashlib,json,sys
r=Path('.');tag,g=sys.argv[1:];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=r/'reports'/f'{tag}_launch.json';a=json.loads(p.read_text());glaunch=json.loads((r/'reports'/f'{g}_launch.json').read_text())
files=set(glaunch['sha256'])|{f'reports/{g}_launch.json',f'reports/{g}/global_checks.json'}
a['sha256'].update({n:sha(r/n) for n in files});a['global_run']=g;a['final_placement_global_verified']=True;p.write_text(json.dumps(a,indent=2)+'\n')
PY
export ANTENNA_PLACEMENT_CHECKER=scripts/check_antenna_drive_placement.py
bash scripts/run_antenna_checks.sh "$tag"
python3 scripts/accept_antenna_drive_finish_phase.py "$tag"
docker stop --timeout 5 "$parent" >/dev/null
docker stop --timeout 5 faultv-routed_antenna_residual_20261027_133836 >/dev/null
