#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_native.exit' EXIT
for budget in 0.014 0.028; do
  tag="pg_ir_${budget/./p}_c"
  docker run --rm --name faultv-w25-pg-native-ir --user 1000:1000 --memory=4500m --cpus=2 -e SRAM_BUDGET_W="$budget" -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" python3 scripts/pg_ir_native_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/pg_ir_state_c.json --run-tag "$tag" config_pg_ir.json > "logs/$tag.log" 2>&1
done
docker run --rm --name faultv-w25-pg-native-stream --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/pg_stream_state_c.json --run-tag pg_stream_b config_pg_stream.json > logs/pg_stream_b.log 2>&1
