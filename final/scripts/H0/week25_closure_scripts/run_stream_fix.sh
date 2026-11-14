#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/stream_fix.exit' EXIT
python3 scripts/prepare_stream_fix.py
docker run --rm --name faultv-w25-stream-fix --user 1000:1000 --memory=3500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_front/working_candidate_state.json --run-tag stream_fix_a config_stream_fix.json > logs/stream_fix.log 2>&1
docker run --rm --name faultv-w25-stream-audit --user 1000:1000 --memory=3000m --cpus=1 -e AUDIT_CORE_GDS=/work/week25_closure/runs/stream_fix_a/1-klayout-streamout/fault_v_asic_top.gds -e AUDIT_REPORT=reports/streamed_SRAM_geometry_fixed.json -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r scripts/audit_stream_macro.py > logs/stream_fix_audit.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
d=json.loads(Path('reports/streamed_SRAM_geometry_fixed.json').read_text())
assert d['all_selected_manufacturing_layers_exact']
PY
