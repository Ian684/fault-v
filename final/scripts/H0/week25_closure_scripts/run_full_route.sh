#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/full_route.exit' EXIT
python3 scripts/prepare_full_route.py
docker run --rm --name faultv-w25-full-route --user 1000:1000 --memory=10000m --cpus=8 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/full_route_state.json --run-tag full_route_a config_full_route.json > logs/full_route.log 2>&1
