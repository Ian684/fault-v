#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?antenna candidate run}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
placement_script="${ANTENNA_PLACEMENT_CHECKER:-scripts/check_antenna_placement.py}"
[[ "$placement_script" == scripts/check_antenna_placement.py || "$placement_script" == scripts/check_antenna_drive_placement.py ]]
export ANTENNA_PLACEMENT_CHECKER="$placement_script"
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
[[ "$(cat "$root/logs/$tag.exit")" == 0 ]]
python3 - "$tag" <<'PY'
import json,sys,os
from pathlib import Path
m=json.loads((Path('runs')/sys.argv[1]/'final/metrics.json').read_text())
assert m['route__drc_errors']==0 and m['route__antenna_violation__count']==0,m
import hashlib
r=Path('.'); tag=sys.argv[1]; p=r/'reports'/tag/'checks_source.json'
assert not p.exists() and not (r.parent/'logs'/f'{tag}_checks.exit').exists(), 'Refuse stale checks'
files=['scripts/run_antenna_checks.sh','scripts/audit_antenna_metadata.py','scripts/check_antenna_placement.py','scripts/check_antenna_signal_connectivity.py','scripts/search_manual_eco.py','scripts/check_placement.py','scripts/check_routes.py','scripts/check_physical.tcl','scripts/check_timing.py','scripts/check_route_drc.py','scripts/native_route_drc.py','scripts/run_sta.sh','scripts/prepare_sta.py','scripts/sta310_cli.py','constraints.sdc']
if os.environ['ANTENNA_PLACEMENT_CHECKER']=='scripts/check_antenna_drive_placement.py':
    files+=['scripts/check_antenna_drive_placement.py','reports/antenna_model/debug_spacing_20261029/drive_reference.json','inputs/antenna_drive_reference.odb']
a={'run':tag,'sha256':{name:hashlib.sha256((r/name).read_bytes()).hexdigest() for name in files},'odb_sha256':hashlib.sha256((r/'runs'/tag/'final/odb/fault_v_asic_top.odb').read_bytes()).hexdigest()}
p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(a,indent=2)+'\n')
PY
docker run --rm --user 1000:1000 --memory=2200m -e "ANTENNA_AUDIT_ODB=/work/routing/runs/$tag/final/odb/fault_v_asic_top.odb" -e "ANTENNA_AUDIT_REPORT=/work/routing/reports/$tag/antenna_model_coverage.json" -v "$root:/work" -w /work/routing "$image" openroad -exit -python scripts/audit_antenna_metadata.py > "$root/logs/${tag}_antenna_coverage.log" 2>&1
bash scripts/run_sta.sh "$tag" routed
docker run --rm --user 1000:1000 --memory=5000m -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/routing "$image" openroad -no_init -no_splash -exit -python "$placement_script" > "$root/logs/${tag}_check_placement.log" 2>&1
docker run --rm --user 1000:1000 --memory=2600m -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/routing "$image" openroad -exit -python scripts/check_antenna_signal_connectivity.py > "$root/logs/${tag}_antenna_signal_connectivity.log" 2>&1
docker run --rm --user 1000:1000 --memory=3000m -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/routing "$image" openroad -no_init -no_splash -exit -python scripts/check_routes.py > "$root/logs/${tag}_check_routes.log" 2>&1
docker run --rm --user 1000:1000 --memory=3000m -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/routing "$image" openroad -no_init -no_splash -exit scripts/check_physical.tcl > "$root/logs/${tag}_physical.log" 2>&1
python3 scripts/check_timing.py "$tag"
python3 scripts/check_route_drc.py "$tag"
printf '0\n' > "$root/logs/${tag}_checks.exit"
echo "ANTENNA CANDIDATE PHYSICAL / EXTRACTED RC / TT TIMING CHECKS PASSED: $tag"
