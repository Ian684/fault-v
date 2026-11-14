#!/usr/bin/env bash
set -euo pipefail
cd <HOME>/fault-v-asic/design
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --user "$(id -u):$(id -g)" -v <HOME>/fault-v-asic:/work -w /work/design "$IMAGE" librelane --pdk-root /work/pdk --pdk sky130A --scl sky130_fd_sc_hd --to OpenROAD.STAPrePNR --run-tag tt_slew config_slew.json > <HOME>/fault-v-asic/logs/tt_slew.log 2>&1
