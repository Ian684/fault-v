#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > ../logs/postroute_repair1.exit' EXIT
[[ ! -e runs/postroute_repair1 && ! -e ../logs/postroute_repair1.log ]]
python3 scripts/check_inputs.py
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --name faultv-actual-rc-repair --user "$(id -u):$(id -g)" --memory=6000m --memory-swap=6000m --cpus=8 -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/actual_rc_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/actual_rc_state.json --run-tag postroute_repair1 config_actual_rc.json > "$root/logs/postroute_repair1.log" 2>&1
