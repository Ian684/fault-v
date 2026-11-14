#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/clean_signal_probe.exit' EXIT
python3 scripts/prepare_clean_signal_probe.py
bash scripts/run_native_flow.sh clean_signal_rc_a config_clean_signal_probe_rc.json clean_signal_probe_state.json scripts/native_librelane_cli.py 5000m 2
python3 scripts/prepare_clean_signal_sta.py
bash scripts/run_native_flow.sh clean_signal_sta_a config_clean_signal_sta.json clean_signal_sta_state.json /work/routing/scripts/sta310_cli.py 3000m 1
