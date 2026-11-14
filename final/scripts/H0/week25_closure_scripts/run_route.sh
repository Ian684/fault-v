#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/route.exit' EXIT
docker run --rm --name faultv-w25-reguide --user 1000:1000 --memory=5000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/reguide_minimal.py > logs/reguide.log 2>&1
docker run --rm --name faultv-w25-route --user 1000:1000 --memory=12000m --cpus=4 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/route_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/route_state.json --run-tag minimal_route_a config_route.json > logs/route.log 2>&1
