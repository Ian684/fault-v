#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_stream.exit' EXIT
docker run --rm --name faultv-w25-pg-export --user 1000:1000 --memory=2200m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_pg_stream.py > logs/pg_stream_prepare.log 2>&1
docker run --rm --name faultv-w25-pg-stream --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/pg_stream_state.json --run-tag pg_stream_a config_pg_stream.json > logs/pg_stream.log 2>&1
