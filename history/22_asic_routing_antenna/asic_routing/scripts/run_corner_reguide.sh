#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > ../logs/routed_corner_reguide.exit' EXIT
[[ ! -e runs/routed_corner_reguide && ! -e ../logs/routed_corner_reguide.log ]]
python3 scripts/check_inputs.py
python3 - <<'PY'
from pathlib import Path
import hashlib,json
r=Path(".");s=json.loads((r/"reports/corner_reguide_input.json").read_text())
assert s["cells_and_logical_graph_unchanged"] and s["other_wires_unchanged"] and s["guides_match_new_global"]
assert len(s["removed_nets"])==16 and s["retained_wire_count"]==41298
for name,key in [(s["source"],"source_sha256"),(s["global_source"],"global_source_sha256"),(s["derived"],"derived_sha256")]:
 assert hashlib.sha256((r/name).read_bytes()).hexdigest()==s[key]
PY
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --name faultv-corner-reguide --user "$(id -u):$(id -g)" --memory=6000m --memory-swap=6000m --cpus=8 -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/corner_reguide_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/corner_reguide_state.json --run-tag routed_corner_reguide config_corner_reguide.json > "$root/logs/routed_corner_reguide.log" 2>&1
bash scripts/run_checks.sh global_corner_reserve routed_corner_reguide routed
