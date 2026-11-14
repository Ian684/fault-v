#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
trap 'rc=$?; printf "%s\n" "$rc" > logs/projected67_sta.exit' EXIT
docker run --rm --name faultv-w25-projected67-sta --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302 python3 /work/routing/scripts/sta310_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/projected67_sta_state.json --run-tag projected67_sta_a config_probe50_sta.json > logs/projected67_sta.log 2>&1
