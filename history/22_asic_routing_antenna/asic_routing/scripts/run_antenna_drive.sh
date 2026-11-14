#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?new driver repair run tag}"
global_tag="${2:?matching new global run tag}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ && "$global_tag" =~ ^[A-Za-z0-9_]+$ && ! -e "runs/$tag" && ! -e "runs/$global_tag" ]]
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
parent=faultv-routed_antenna_checkpoint_20261029_151959
finish() {
    result=$?
    trap - EXIT
    docker stop --timeout 5 "faultv-$tag" >/dev/null 2>&1 || true
    docker stop --timeout 5 "faultv-$global_tag" >/dev/null 2>&1 || true
    if [[ "$result" != 0 ]]; then docker unpause "$parent" >/dev/null 2>&1 || true; fi
    printf '%s\n' "$result" > "../logs/${tag}_followup.exit"
    return "$result"
}
trap finish EXIT
python3 scripts/check_inputs.py
[[ "$(docker inspect -f '{{.State.Running}} {{.State.Paused}}' "$parent")" == 'true true' ]]
python3 - "$global_tag" <<'PY'
from pathlib import Path
import datetime,hashlib,json,sys
r=Path('.');tag=sys.argv[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();receipt='reports/antenna_model/debug_spacing_20261029/drive_input.json';a=json.loads((r/receipt).read_text());assert a['pass'] and a['same_Liberty_function_and_pin_contract'] and a['placement_overlap_negative_control_detected']
assert sha(r/a['global_input'])==a['global_input_sha256']
files=[receipt,'scripts/prepare_antenna_drive.py','scripts/antenna_corridor_global_cli.py','scripts/grt_antenna_corridor.tcl','scripts/check_global.py','scripts/run_antenna_drive.sh','antenna_drive_global_state.json','config_antenna_drive_global.json',a['global_input']]
record={'accepted':False,'run':tag,'input':a['global_input'],'input_sha256':a['global_input_sha256'],'config':'config_antenna_drive_global.json','state':'antenna_drive_global_state.json','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':{n:sha(r/n) for n in files},'scope':'Actual global route after exactly one equivalent driver resize; no antenna insertion or other circuit edit.'}
(r/'reports'/f'{tag}_launch.json').write_text(json.dumps(record,indent=2)+'\n')
PY
set +e
timeout --signal=TERM --kill-after=10 600 docker run --rm --name "faultv-$global_tag" --user 1000:1000 --memory=3000m --cpus=2 -v "$root:/work" -w /work/routing "$image" python3 scripts/antenna_corridor_global_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/antenna_drive_global_state.json --run-tag "$global_tag" config_antenna_drive_global.json > "$root/logs/$global_tag.log" 2>&1
result=$?
printf '%s\n' "$result" > "$root/logs/$global_tag.exit"
[[ "$result" == 0 ]] || exit "$result"
set -e
python3 scripts/check_global.py "$global_tag"
docker run --rm --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/routing "$image" openroad -exit -python scripts/reguide_antenna_drive.py "$global_tag" > "$root/logs/${tag}_reguide.log" 2>&1
python3 - "$tag" "$global_tag" <<'PY'
from pathlib import Path
import datetime,hashlib,json,sys
r=Path('.');tag,g=sys.argv[1:];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();folder='reports/antenna_model/debug_spacing_20261029'
receipt=f'{folder}/drive_guided_input.json';a=json.loads((r/receipt).read_text());assert a['pass'] and a['global_run']==g and a['global_overflow']==0 and sha(r/a['derived'])==a['derived_sha256']
c=json.loads((r/'config_antenna_drive.json').read_text());assert c['CLOCK_PERIOD']==40 and c['ERROR_ON_TR_DRC'] and c['DRT_ANTENNA_REPAIR_ITERS']==0 and c['DRT_OPT_ITERS']==64 and c['DRT_THREADS']==8
(r/f'config_{tag}.json').write_text(json.dumps(c,indent=2)+'\n')
files=['scripts/antenna_drive_cli.py','scripts/drt_antenna_drive.tcl','scripts/run_antenna_drive.sh','scripts/prepare_antenna_drive.py','scripts/reguide_antenna_drive.py','scripts/check_antenna_drive_placement.py','scripts/check_antenna_placement.py','scripts/run_antenna_checks.sh','scripts/accept_antenna_drive_phase.py','scripts/accept_antenna_both8_phase.py','scripts/accept_antenna_phase.py','scripts/prepare_desktop_checkpoint45.py','scripts/prepare_cold_corner_reguide.py','scripts/prepare_antenna_one_spacing.py','scripts/search_manual_eco.py','scripts/prepare_desktop_local_bridge_flat.py','antenna_drive_state.json',f'config_{tag}.json',receipt,f'{folder}/drive_input.json',f'{folder}/drive_reference.json',f'{folder}/spacing_input.json','inputs/antenna_drive_reference.odb','inputs/antenna_drive_partial.odb','inputs/antenna_spacing_source59.odb','inputs/antenna_spacing_native.odb','runs/routed_antenna_spacing_20261029_1700/final/odb/fault_v_asic_top.odb','runs/routed_antenna_spacing_20261029_1700/1-openroad-detailedrouting/intervention_pair.json','reports/antenna_model/sram_antenna_model.json','macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef',f'reports/{g}/global_checks.json',f'reports/{g}_launch.json']
global_launch=json.loads((r/f'reports/{g}_launch.json').read_text());files=sorted(set(files)|set(global_launch['sha256']))
launch={'accepted':False,'run':tag,'global_run':g,'cli':'scripts/antenna_drive_cli.py','state':'antenna_drive_state.json','config':f'config_{tag}.json','placement_checker':'scripts/check_antenna_drive_placement.py','distribution':'Ubuntu-D','threads':8,'memory_mb':6500,'input_sha256':a['derived_sha256'],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':{n:sha(r/n) for n in files},'scope':'Retain the DRC/antenna-zero bend repair; resize one Liberty-equivalent o21ai_2 to o21ai_4 at unchanged location/orientation. Fresh access and four-net reroute from actual matching zero-overflow guides. All original functional, physical, antenna, DRC, RC and TT constraints mandatory.'}
(r/'reports'/f'{tag}_launch.json').write_text(json.dumps(launch,indent=2)+'\n')
p=r/'WORK_STATE.json';s=json.loads(p.read_text());s.update(active_routed=tag,status='antenna_drive_electrical_repair',week24_complete=False,antenna_closure_complete=False,ppa_ready=False,current_live_jobs=[{'run':tag,'distribution':'Ubuntu-D','status':'native_running','accepted':False},{'run':'routed_antenna_checkpoint_20261029_151959','status':'paused_preserved','accepted':False},{'run':'routed_antenna_residual_20261027_133836','status':'paused_preserved','accepted':False}]);s['antenna_work'].update(candidate=tag,status='single_driver_repair',current_stage='single_driver_four_net_reroute',driver_repair_launch=f'reports/{tag}_launch.json',preceding_zero_DRC_zero_antenna_run='routed_antenna_spacing_20261029_1700',preceding_electrical_failure={'max_slew':5,'max_cap':1,'shared_driver':'_44992_/Y'});p.write_text(json.dumps(s,indent=2)+'\n')
PY
set +e
docker run --rm --name "faultv-$tag" --user 1000:1000 --memory=6500m --memory-swap=6500m --cpus=8 -v "$root:/work" -w /work/routing "$image" python3 scripts/antenna_drive_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/antenna_drive_state.json --run-tag "$tag" "config_${tag}.json" > "$root/logs/$tag.log" 2>&1
result=$?
printf '%s\n' "$result" > "$root/logs/$tag.exit"
python3 - "$tag" "$result" <<'PY'
from pathlib import Path
import json,sys
p=Path('reports')/(sys.argv[1]+'_launch.json');a=json.loads(p.read_text());a['native_exit']=int(sys.argv[2]);p.write_text(json.dumps(a,indent=2)+'\n')
PY
[[ "$result" == 0 ]] || exit "$result"
set -e
export ANTENNA_PLACEMENT_CHECKER=scripts/check_antenna_drive_placement.py
bash scripts/run_antenna_checks.sh "$tag"
python3 scripts/accept_antenna_drive_phase.py "$tag"
docker stop --timeout 5 "$parent" >/dev/null
docker stop --timeout 5 faultv-routed_antenna_residual_20261027_133836 >/dev/null
