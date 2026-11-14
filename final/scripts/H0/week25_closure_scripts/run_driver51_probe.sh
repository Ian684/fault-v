#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/driver51_probe.exit' EXIT
python3 scripts/prepare_driver51_probe.py
bash scripts/run_native_flow.sh driver51_rc_a config_driver51_probe_rc.json driver51_probe_state.json scripts/native_librelane_cli.py 5000m 2
python3 scripts/prepare_driver51_sta.py
bash scripts/run_native_flow.sh driver51_sta_a config_driver51_sta.json driver51_sta_state.json /work/routing/scripts/sta310_cli.py 3000m 1
