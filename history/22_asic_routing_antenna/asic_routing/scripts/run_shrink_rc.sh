#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > ../logs/shrink_rc.exit' EXIT
[[ ! -e runs/shrink_rc && ! -e ../logs/shrink_rc.log ]]
python3 scripts/check_inputs.py
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --name faultv-shrink-rc --user "$(id -u):$(id -g)" --memory=6000m --memory-swap=6000m --cpus=8 -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/shrink_rc_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/shrink_rc_state.json --run-tag shrink_rc config_direct_rc.json > "$root/logs/shrink_rc.log" 2>&1
