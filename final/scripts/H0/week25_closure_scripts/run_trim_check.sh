#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/trim_check.exit' EXIT
python3 scripts/prepare_trim_check.py
docker run --rm --name faultv-w25-trim-full-check --user 1000:1000 --memory=5500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/correct_stream_state.json --run-tag trimmed_full_drc_a config_trim_check.json > logs/trim_full_DRC.log 2>&1
docker run --rm --user 1000:1000 --memory=3000m --cpus=1 -e AUDIT_MACRO_GDS=/work/week25_closure/macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim.gds -e AUDIT_CORE_GDS=/work/week25_closure/runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds -e AUDIT_REPORT=reports/streamed_SRAM_geometry_trimmed.json -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r scripts/audit_stream_macro.py > logs/trim_stream_audit.log 2>&1
python3 - <<'PY'
from pathlib import Path
import json
assert json.loads(Path('reports/streamed_SRAM_geometry_trimmed.json').read_text())['all_selected_manufacturing_layers_exact']
metrics=json.loads(Path('runs/trimmed_full_drc_a/final/metrics.json').read_text())
assert metrics['klayout__drc_error__count']==0
PY
