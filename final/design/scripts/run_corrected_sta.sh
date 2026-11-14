#!/usr/bin/env bash
set -euo pipefail
cd <HOME>/fault-v-asic/design
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --user "$(id -u):$(id -g)" -v <HOME>/fault-v-asic:/work -w /work/design "$IMAGE" bash -c 'export PATH="/work/tools/sta_fixed_bin:$PATH"; exec librelane "$@"' fault-v --pdk-root /work/pdk --pdk sky130A --scl sky130_fd_sc_hd --only OpenROAD.STAPrePNR --with-initial-state /work/design/runs/tt_electrical/12-openroad-staprepnr/state_in.json --run-tag tt_corrected config_electrical.json > <HOME>/fault-v-asic/logs/tt_corrected.log 2>&1
