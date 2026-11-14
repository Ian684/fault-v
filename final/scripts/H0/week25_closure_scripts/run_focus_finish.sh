#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
trap 'rc=$?; printf "%s\n" "$rc" > logs/focus_finish.exit' EXIT
docker run --rm --name faultv-w25-focus-finish --user 1000:1000 --memory=4800m --cpus=4 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302 python3 scripts/focus_finish_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/focus_finish_state.json --run-tag focus_finish_a config_focus_finish.json > logs/focus_finish.log 2>&1
