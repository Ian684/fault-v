#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > ../logs/routed_pin_checkpoint.exit' EXIT
[[ ! -e runs/routed_pin_checkpoint && ! -e ../logs/routed_pin_checkpoint.log ]]
python3 scripts/check_inputs.py
python3 - <<'PY'
from pathlib import Path
import hashlib,json
r=Path(".");s=json.loads((r/"reports/pin_spread_checkpoint_input.json").read_text())
assert s["source_native_drc"]==707
assert hashlib.sha256((r/s["source"]).read_bytes()).hexdigest()==s["source_sha256"]
assert hashlib.sha256((r/s["source_report"]).read_bytes()).hexdigest()==s["source_report_sha256"]
assert (r/s["source_report"]).read_text().count("violation type:")==707
PY
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --name faultv-pin-checkpoint --user "$(id -u):$(id -g)" --memory=6000m --memory-swap=6000m --cpus=8 -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/corner_reguide_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/pin_spread_checkpoint_state.json --run-tag routed_pin_checkpoint config_corner_reguide.json > "$root/logs/routed_pin_checkpoint.log" 2>&1
bash scripts/run_checks.sh global_pin_spread routed_pin_checkpoint routed
