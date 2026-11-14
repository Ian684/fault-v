#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/selected_w_pipeline.exit' EXIT
while [[ ! -f logs/antenna_native_w_checks.exit ]]; do
  if [[ -f logs/native_group_w.exit ]]; then
    test "$(cat logs/native_group_w.exit)" = 0
  fi
  sleep 2
done
test "$(cat logs/antenna_native_w_checks.exit)" = 0
bash scripts/run_final_selected_w.sh native_group_w antenna_native_w
python3 scripts/verify_final_ir_results.py
