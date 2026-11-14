#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
trap 'rc=$?; printf "%s\n" "$rc" > logs/protected_cached.exit' EXIT
docker run --rm --name faultv-w25-protected-cached --user 1000:1000 --memory=4800m --cpus=4 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302 python3 scripts/protected_cached_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/protected_cached_state.json --run-tag protected_cached_a config_protected_route.json > logs/protected_cached.log 2>&1
