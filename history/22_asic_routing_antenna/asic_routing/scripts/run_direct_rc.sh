#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > ../logs/direct_rc1.exit' EXIT
[[ ! -e runs/direct_rc1 && ! -e ../logs/direct_rc1.log ]]
python3 scripts/check_inputs.py
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --name faultv-actual-rc-repair --user "$(id -u):$(id -g)" --memory=6000m --memory-swap=6000m --cpus=8 -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/direct_rc_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/actual_rc_state.json --run-tag direct_rc1 config_direct_rc.json > "$root/logs/direct_rc1.log" 2>&1
