#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/cached_prepare.exit' EXIT
docker run --rm --name faultv-w25-cached-prepare --user 1000:1000 --memory=5500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_cached_route.py > logs/cached_prepare.log 2>&1
docker run --rm --name faultv-w25-cached-global --user 1000:1000 --memory=5000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/cached_global_state.json --run-tag cached_global_a config_cached_global.json > logs/cached_global.log 2>&1
