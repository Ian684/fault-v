#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/fill_rcx_control.exit' EXIT
docker run --rm --user 1000:1000 --memory=2500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_fill_rcx_control.py > logs/fill_rcx_prepare.log 2>&1
docker run --rm --name faultv-w25-fill-rcx-control --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/fill_rcx_state.json --run-tag fill_rcx_control_a config_fill_rcx.json > logs/fill_rcx_control.log 2>&1
