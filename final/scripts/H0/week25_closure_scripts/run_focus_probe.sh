#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/focus_probe.exit' EXIT
docker run --rm --name faultv-w25-focus_probe-rc --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/focus_probe_state.json --run-tag focus_probe_rc_a config_focus_probe_rc.json > logs/focus_probe_rc.log 2>&1
python3 scripts/prepare_focus_probe_sta.py
docker run --rm --name faultv-w25-focus_probe-sta --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 /work/routing/scripts/sta310_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/focus_probe_sta_state.json --run-tag focus_probe_sta_a config_focus_probe_sta.json > logs/focus_probe_sta.log 2>&1
