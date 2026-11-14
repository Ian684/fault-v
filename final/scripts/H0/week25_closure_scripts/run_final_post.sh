#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/final_post.exit' EXIT
python3 scripts/prepare_final_post.py
bash scripts/run_native_flow.sh focus_post_a config_focus_post.json final_post_state.json scripts/native_librelane_cli.py 7000m 2
python3 scripts/prepare_focus_post_sta.py
bash scripts/run_native_flow.sh focus_post_sta_a config_focus_post_sta.json focus_post_sta_state.json /work/routing/scripts/sta310_cli.py 3000m 1
