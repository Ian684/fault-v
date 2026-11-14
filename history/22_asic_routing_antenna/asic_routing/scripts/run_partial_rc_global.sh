#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > ../logs/global_direct_rc.exit' EXIT
[[ ! -e runs/global_direct_rc && ! -e ../logs/global_direct_rc.log ]]
python3 scripts/check_inputs.py
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --name faultv-global-direct-rc --user "$(id -u):$(id -g)" --memory=6000m --memory-swap=6000m --cpus=8 -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/partial_rc_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/partial_rc_state.json --run-tag global_direct_rc config_partial_rc.json > "$root/logs/global_direct_rc.log" 2>&1
python3 scripts/check_global.py global_direct_rc
