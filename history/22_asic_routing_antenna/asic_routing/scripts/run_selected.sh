#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?Supply a fresh alphanumeric/underscore run tag}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ && ! -e "runs/$tag" && ! -e "reports/$tag" && ! -e "../logs/$tag.log" ]]
python3 scripts/check_inputs.py
mapfile -t chosen < <(python3 - "$tag" <<'PY'
from pathlib import Path
import json,hashlib,re,sys
r=Path('.'); s=json.loads((r/'selected_flow.json').read_text())
assert s['accepted'] and s['antenna_closure']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
launch=json.loads((r/'reports'/f"{s['routed_run']}_launch.json").read_text());assert launch['accepted']
for name,digest in launch['sha256'].items():assert sha(r/name)==digest,name
c=json.loads((r/s['config']).read_text())
assert c['CLOCK_PERIOD']==40 and c['ERROR_ON_TR_DRC'] is True
assert c['DRT_ANTENNA_REPAIR_ITERS']==s['antenna_repair_iterations'] and 0<=s['antenna_repair_iterations']<=5 and c['DRT_THREADS']==s['threads']
assert 0<s['threads']<=s['container_cpus']==launch['threads']
frozen=json.loads((r/'input_identity.json').read_text())['sha256']
for name in [s['cli'],s['config'],s['state']]:
 assert re.fullmatch(r'[A-Za-z0-9_./]+',name) and name in frozen and sha(r/name)==frozen[name],name
state=json.loads((r/s['state']).read_text());prefix='/work/routing/';assert state['odb'].startswith(prefix)
source=state['odb'].removeprefix(prefix);assert source in frozen and sha(r/source)==frozen[source]==launch['input_sha256']
tag=sys.argv[1];config=f'config_{tag}.json';(r/config).write_text(json.dumps(c,indent=2)+'\n')
launch.update(accepted=False,run=tag,config=config,replay_of=s['routed_run']);launch.pop('native_exit',None);launch.pop('pipeline_exit',None);launch['sha256'][config]=sha(r/config)
(r/'reports'/f'{tag}_launch.json').write_text(json.dumps(launch,indent=2)+'\n')
budget=launch.get('budget_seconds')
assert budget is None or isinstance(budget,int) and budget>0
checker=s.get('placement_checker','scripts/check_antenna_placement.py')
assert checker in ['scripts/check_antenna_placement.py','scripts/check_antenna_drive_placement.py'] and checker in frozen
for value in [s['cli'],config,s['state'],s['container_cpus'],s['memory_mb'],budget or 0,checker]:print(value)
PY
)
[[ ${#chosen[@]} == 7 ]]
root="$(cd .. && pwd)"
mkdir -p "$root/logs"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
# shortcut: replay starts at the exact frozen ECO input; an RTL rebuild uses upstream flows.
set +e
limit=()
[[ "${chosen[5]}" == 0 ]] || limit=(timeout --signal=TERM --kill-after=10 "${chosen[5]}")
"${limit[@]}" docker run --rm --name "faultv-$tag" --user "$(id -u):$(id -g)" --cpus="${chosen[3]}" --memory="${chosen[4]}m" --memory-swap="${chosen[4]}m" -v "$root:/work" -w /work/routing "$image" python3 "${chosen[0]}" --pdk-root /work/pdk --with-initial-state "/work/routing/${chosen[2]}" --run-tag "$tag" "${chosen[1]}" > "$root/logs/$tag.log" 2>&1
result=$?
docker stop --timeout 5 "faultv-$tag" >/dev/null 2>&1 || true
printf '%s\n' "$result" > "$root/logs/$tag.exit"
python3 - "$tag" "$result" <<'PY'
from pathlib import Path
import json,sys
p=Path('reports')/(sys.argv[1]+'_launch.json');a=json.loads(p.read_text());a['native_exit']=int(sys.argv[2]);p.write_text(json.dumps(a,indent=2)+'\n')
PY
[[ "$result" == 0 ]] || exit "$result"
set -e
export ANTENNA_PLACEMENT_CHECKER="${chosen[6]}"
bash scripts/run_antenna_checks.sh "$tag"
printf 'Replay passed all routing, antenna, physical, RC and TT gates: %s\n' "$tag"
