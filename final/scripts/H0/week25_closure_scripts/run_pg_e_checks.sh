#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_e_checks.exit' EXIT
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-pg-e-prep --user 1000:1000 --memory=3000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_pg_e_checks.py > logs/pg_e_prep.log 2>&1
bash scripts/run_native_flow.sh pg_e_stream_a config_pg_e_stream.json pg_e_stream_state.json scripts/native_librelane_cli.py 4000m 2
for budget in 0.014 0.028; do
  SRAM_BUDGET_W="$budget" bash scripts/run_native_ir_flow.sh "pg_e_ir_${budget/./p}_a" config_pg_ir.json pg_e_ir_state.json scripts/pg_ir_native_cli.py 4000m 2
done
python3 scripts/audit_pg_em.py 'pg_e_ir_{budget}_a' reports/runtime_pg_compact_e_odb.json reports/pg_e_em_resistor_audit.json > logs/pg_e_em_audit.log 2>&1
