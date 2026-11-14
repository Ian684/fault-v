#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_b.exit' EXIT
docker run --rm --name faultv-w25-pg-b-prepare --user 1000:1000 --memory=2500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_pg_b.py > logs/pg_b_prepare.log 2>&1
for budget in 0.014 0.028; do
  tag="pg_ir_${budget/./p}_b"
  docker run --rm --name faultv-w25-pg-b-ir --user 1000:1000 --memory=4500m --cpus=2 -e SRAM_BUDGET_W="$budget" -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/pg_ir_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/pg_ir_state_b.json --run-tag "$tag" config_pg_ir.json > "logs/$tag.log" 2>&1
done
docker run --rm --name faultv-w25-pg-b-stream --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/pg_stream_state_b.json --run-tag pg_stream_b config_pg_stream.json > logs/pg_stream_b.log 2>&1
