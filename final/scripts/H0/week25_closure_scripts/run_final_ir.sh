#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/final_ir.exit' EXIT
python3 scripts/prepare_final_ir.py
for budget in 0.014 0.028; do
  SRAM_BUDGET_W="$budget" bash scripts/run_native_ir_flow.sh "final_ir_${budget/./p}_a" config_final_ir.json final_ir_state.json scripts/final_ir_cli.py 4000m 2
done
python3 scripts/audit_pg_em.py 'final_ir_{budget}_a' reports/runtime_final_filled_odb.json reports/final_em_resistor_audit.json > logs/final_em_audit.log 2>&1
