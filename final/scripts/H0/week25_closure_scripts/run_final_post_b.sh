#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/final_post_b.exit' EXIT
python3 scripts/prepare_final_post_b.py
bash scripts/run_native_flow.sh focus_post_b config_focus_post_b.json final_post_state_b.json scripts/native_librelane_cli.py 7000m 2
python3 scripts/prepare_focus_post_sta_b.py
bash scripts/run_native_flow.sh focus_post_sta_b config_focus_post_sta_b.json focus_post_sta_b_state.json /work/routing/scripts/sta310_cli.py 3000m 1
