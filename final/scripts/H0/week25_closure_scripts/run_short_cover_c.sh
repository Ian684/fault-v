#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-short-c-prep --user 1000:1000 --memory=3000m --cpus=2 -v /mnt/e/Codex/Fault_V_W24_Transfer/work/fault-v-asic:/work -v /var/tmp/faultv-w25-native-runs/short_cover_b:/route_b:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_short_cover_c.py > logs/short_cover_c_prep.log 2>&1
bash scripts/run_native_flow.sh short_cover_c config_short_cover_c.json short_cover_c_state.json scripts/short_cover_c_cli.py 7000m 8
