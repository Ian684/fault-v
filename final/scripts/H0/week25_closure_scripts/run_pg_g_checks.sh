#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_g_checks.exit' EXIT
python3 -c 'import json;d=json.load(open("reports/pg_g_independent.json"));g=json.load(open("reports/pg_g_geometry_binding.json"));assert d["unresolved_count"]==0 and d["odb_sha256"]==g["output_sha256"]'
bash scripts/run_native_flow.sh pg_g_stream_a config_pg_g_stream.json pg_g_stream_state.json scripts/native_librelane_cli.py 4000m 2
for budget in 0.014 0.028; do
  SRAM_BUDGET_W="$budget" bash scripts/run_native_ir_flow.sh "pg_g_ir_${budget/./p}_a" config_pg_ir.json pg_g_ir_state.json scripts/pg_ir_native_cli.py 4000m 2
done
python3 scripts/audit_pg_em.py 'pg_g_ir_{budget}_a' reports/runtime_pg_compact_g_odb.json reports/pg_g_em_resistor_audit.json > logs/pg_g_em_audit.log 2>&1
