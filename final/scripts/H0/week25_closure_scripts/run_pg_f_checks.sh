#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_f_checks.exit' EXIT
python3 -c 'import json;d=json.load(open("reports/pg_f_independent.json"));g=json.load(open("reports/pg_f_geometry_binding.json"));assert d["unresolved_count"]==0 and d["odb_sha256"]==g["output_sha256"]'
bash scripts/run_native_flow.sh pg_f_stream_a config_pg_f_stream.json pg_f_stream_state.json scripts/native_librelane_cli.py 4000m 2
for budget in 0.014 0.028; do
  SRAM_BUDGET_W="$budget" bash scripts/run_native_ir_flow.sh "pg_f_ir_${budget/./p}_a" config_pg_ir.json pg_f_ir_state.json scripts/pg_ir_native_cli.py 4000m 2
done
python3 scripts/audit_pg_em.py 'pg_f_ir_{budget}_a' reports/runtime_pg_compact_f_odb.json reports/pg_f_em_resistor_audit.json > logs/pg_f_em_audit.log 2>&1
