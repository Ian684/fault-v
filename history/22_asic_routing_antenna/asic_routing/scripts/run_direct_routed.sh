#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > ../logs/routed_direct_rc.exit' EXIT
[[ ! -e runs/routed_direct_rc && ! -e ../logs/routed_direct_rc.log ]]
python3 scripts/check_inputs.py
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --name faultv-direct-rc-routed --user "$(id -u):$(id -g)" --memory=6000m --memory-swap=6000m --cpus=8 -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/corner_reguide_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/direct_rc_routed_state.json --run-tag routed_direct_rc config_corner_reguide.json > "$root/logs/routed_direct_rc.log" 2>&1
bash scripts/run_checks.sh global_direct_rc2 routed_direct_rc routed
