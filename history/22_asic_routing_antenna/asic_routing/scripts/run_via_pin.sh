#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > ../logs/routed_via_pin.exit' EXIT
[[ ! -e runs/routed_via_pin && ! -e ../logs/routed_via_pin.log ]]
python3 scripts/check_inputs.py
python3 - <<'PY'
from pathlib import Path
import hashlib,json
r=Path(".");s=json.loads((r/"reports/three_net_reroute_input.json").read_text())
assert s["cells_and_logical_graph_unchanged"] and s["other_wire_lengths_unchanged"] and s["original_guides_retained"]
assert len(s["removed_nets"])==3 and s["retained_wires"]==41311
for name,key in [(s["source"],"source_sha256"),(s["derived"],"derived_sha256")]:
 assert hashlib.sha256((r/name).read_bytes()).hexdigest()==s[key]
PY
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --name faultv-via-pin --user "$(id -u):$(id -g)" --memory=6000m --memory-swap=6000m --cpus=8 -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/via_pin_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/three_net_reroute_state.json --run-tag routed_via_pin config_corner_reguide.json > "$root/logs/routed_via_pin.log" 2>&1
bash scripts/run_checks.sh global_buffered routed_via_pin routed
