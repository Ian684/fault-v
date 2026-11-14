#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?Supply a new run tag}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
[[ ! -e "runs/$tag" && ! -e "reports/${tag}_launch.json" && ! -e "../logs/$tag.log" ]]
python3 scripts/run_desktop.py --check-only
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
python3 - "$tag" <<'PY'
from pathlib import Path
import json,sys,hashlib,datetime
r=Path('.'); tag=sys.argv[1]
c=json.loads((r/'config_routed_desktop_20261021_172627.json').read_text()); assert c['DRT_THREADS']==16
original=json.loads((r/'config_corner_reguide.json').read_text())
assert {k:v for k,v in c.items() if k!='DRT_THREADS'}=={k:v for k,v in original.items() if k!='DRT_THREADS'}
c['RT_CLOCK_MIN_LAYER']='met4'
c['RT_CLOCK_MAX_LAYER']='met5'
(r/f'config_{tag}.json').write_text(json.dumps(c,indent=2)+'\n')
audit=json.loads((r/'reports/desktop_electrical_native_input.json').read_text()); assert hashlib.sha256((r/'inputs/desktop_electrical_native.odb').read_bytes()).hexdigest()==audit['derived_sha256']
files=['scripts/desktop_fresh_cli.py','scripts/drt_desktop_fresh.tcl',f'config_{tag}.json','desktop_electrical_native_state.json']
a={'accepted':False,'run':tag,'global_run':'global_desktop_electrical','cli':files[0],'config':files[2],'state':files[3],'threads':16,'memory_mb':12000,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sha256':{p:hashlib.sha256((r/p).read_bytes()).hexdigest() for p in files}}
(r/f'reports/{tag}_launch.json').write_text(json.dumps(a,indent=2)+'\n')
PY
set +e
docker run --rm --name "faultv-desktop-$tag" --user "$(id -u):$(id -g)" --memory=12000m --memory-swap=12000m --cpus=16 -v "$root:/work" -w /work/routing "$image" python3 scripts/desktop_fresh_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/desktop_electrical_native_state.json --run-tag "$tag" "config_${tag}.json" > "$root/logs/$tag.log" 2>&1
result=$?
printf '%s\n' "$result" > "$root/logs/$tag.exit"
if [[ "$result" == 0 ]]; then
 bash scripts/run_checks.sh global_desktop_electrical "$tag" routed > "$root/logs/${tag}_checks.log" 2>&1
 result=$?
fi
printf '%s\n' "$result" > "$root/logs/${tag}_pipeline.exit"
python3 - "$tag" "$result" <<'PY'
from pathlib import Path
import json,sys,datetime
p=Path('reports')/(sys.argv[1]+'_launch.json'); a=json.loads(p.read_text()); a['pipeline_exit']=int(sys.argv[2]); a['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
if a['pipeline_exit']==0:
 s=json.loads(Path('accepted_summary.json').read_text()); assert s['accepted'] and s['routed_run']==sys.argv[1]; a['accepted']=True
p.write_text(json.dumps(a,indent=2)+'\n')
PY
exit "$result"
