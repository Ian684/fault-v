#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_d_lvs.exit' EXIT
docker run --rm --name faultv-w25-pg-d-lvs --user 1000:1000 --memory=7000m --cpus=2 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302 python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/pg_d_lvs_state.json --run-tag pg_d_lvs_a config_pg_d_lvs.json > logs/pg_d_lvs.log 2>&1
