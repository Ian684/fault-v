#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
task_root="$(cd .. && pwd)"
run_tag="${1:-tt_reproduce}"
mkdir -p ../logs
docker run --rm --user "$(id -u):$(id -g)" -v "$task_root:/work" -w /work/design "$IMAGE" python3 scripts/sta310_cli.py --pdk-root /work/pdk --pdk sky130A --scl sky130_fd_sc_hd --to OpenROAD.STAPrePNR --run-tag "$run_tag" config.json > "../logs/$run_tag.log" 2>&1
python3 scripts/check_eco.py
python3 scripts/prepare_reload.py "$run_tag"
docker run --rm --user "$(id -u):$(id -g)" -v "$task_root:/work" -w /work/design "$IMAGE" python3 scripts/sta310_cli.py --pdk-root /work/pdk --pdk sky130A --scl sky130_fd_sc_hd --only OpenROAD.STAPrePNR --with-initial-state /work/design/eco/reload_state.json --run-tag "${run_tag}_reload" config_reload.json > "../logs/${run_tag}_reload.log" 2>&1
python3 scripts/accept_closed.py "${run_tag}_reload"
