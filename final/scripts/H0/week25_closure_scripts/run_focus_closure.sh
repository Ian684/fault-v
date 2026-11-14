#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/focus_closure.exit' EXIT
docker run --rm --user 1000:1000 --memory=3500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_focus_closure.py > logs/focus_prepare.log 2>&1
docker run --rm --name faultv-w25-focus-closure --user 1000:1000 --memory=4500m --cpus=4 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/focus_route_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/focus_route_state.json --run-tag focus_route_a config_focus_route.json > logs/focus_route.log 2>&1
