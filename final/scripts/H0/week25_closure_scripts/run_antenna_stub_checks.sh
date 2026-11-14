#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/antenna_stub_checks.exit' EXIT
stem="$1"; [[ "$stem" =~ ^(antenna_stubs_[a-z]|antenna_restore4|antenna_jumper)$ ]]
python3 - "$stem" <<'PY'
import json,sys
from pathlib import Path
stem=sys.argv[1];p=json.loads((Path('reports')/stem/'result.json').read_text())
assert p['antenna_nets']==0 and p.get('diodes_connected_with_checked_stubs',p.get('passive_diodes_added'))==20
assert not (Path('reports')/(stem+'_independent.json')).exists()
PY
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-stubs-independent --user 1000:1000 --memory=4000m --cpus=2 -e "ROUTE_DRC_ODB=/runtime_final/$stem.odb" -e "ROUTE_DRC_REPORT=/work/week25_closure/reports/${stem}_independent.json" -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python /work/routing/scripts/native_route_drc.py > "logs/${stem}_independent.log" 2>&1
docker run --rm --name faultv-w25-stubs-connectivity --user 1000:1000 --memory=2500m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_all_signal_connectivity.py "/runtime_final/$stem.odb" "reports/${stem}_all_connectivity.json" > "logs/${stem}_connectivity.log" 2>&1
python3 scripts/prepare_antenna_stub_export.py "$stem"
bash scripts/run_native_flow.sh antenna_manual_a config_antenna_stub_manual.json antenna_stub_manual_state.json scripts/antenna_stub_export_cli.py 4000m 2
docker run --rm --name faultv-w25-stubs-export-binding --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-native-runs/antenna_manual_a:/work/week25_closure/runs/antenna_manual_a:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_manual_export_binding.py antenna_manual_a "${stem}_independent.json" final_manual_export_binding.json > logs/final_manual_export_binding.log 2>&1
