#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_via_trial.exit' EXIT
docker run --rm --name faultv-w25-pg-via-prepare --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_pg_via_trial.py > logs/pg_via_prepare.log 2>&1
for budget in 0.014 0.028; do
    tag="pg_ir_${budget/./p}_a"
    docker run --rm --name faultv-w25-pg-ir --user 1000:1000 --memory=4500m --cpus=2 -e SRAM_BUDGET_W="$budget" -v "$root:/work" -w /work/week25_closure "$image" python3 /work/week25_signoff/scripts/ir_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/pg_ir_state.json --run-tag "$tag" config_pg_ir.json > "logs/$tag.log" 2>&1
done
