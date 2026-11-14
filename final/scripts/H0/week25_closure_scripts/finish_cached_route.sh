#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/cached_route.exit' EXIT
docker run --rm --user 1000:1000 --memory=2500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/audit_cached_pins.py > logs/cached_pin_audit.log 2>&1
docker run --rm --name faultv-w25-cached-route --user 1000:1000 --memory=11000m --cpus=4 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/cached_route_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/cached_route_state.json --run-tag cached_route_a config_cached_route.json > logs/cached_route.log 2>&1
