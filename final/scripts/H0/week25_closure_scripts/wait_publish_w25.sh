#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/W25_publication.exit' EXIT
while [[ ! -f logs/selected_w_pipeline.exit ]]; do sleep 2; done
test "$(cat logs/selected_w_pipeline.exit)" = 0
python3 scripts/build_w25_closure_report.py
python3 scripts/seal_w25_evidence.py create
python3 scripts/promote_w25_status.py
