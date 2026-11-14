#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
mkdir -p logs reports inputs runs
trap 'rc=$?; printf "%s\n" "$rc" > logs/minimal.exit' EXIT
docker run --rm --name faultv-w25-minimal-prepare --user 1000:1000 --memory=5500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_minimal.py > logs/minimal_prepare.log 2>&1
docker run --rm --name faultv-w25-minimal-global --user 1000:1000 --memory=5500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/global_state.json --run-tag minimal_global_a config_global.json > logs/minimal_global.log 2>&1
