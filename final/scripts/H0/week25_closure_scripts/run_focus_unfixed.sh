#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/focus_unfixed.exit' EXIT
docker run --rm --name faultv-w25-focus-unfixed-audit --user 1000:1000 --memory=2000m --cpus=1 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_focus_unfixed_pins.py > logs/focus_unfixed_pin_audit.log 2>&1
docker run --rm --name faultv-w25-focus-unfixed --user 1000:1000 --memory=4800m --cpus=4 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" python3 scripts/focus_unfixed_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/focus_unfixed_state.json --run-tag focus_unfixed_a config_focus_route.json > logs/focus_unfixed.log 2>&1
