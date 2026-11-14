#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/native12_stream_probe.exit' EXIT
python3 scripts/prepare_native12_stream.py
bash scripts/run_native_flow.sh native12_stream_a config_native12_stream.json native12_stream_state.json scripts/native_librelane_cli.py 5000m 2
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-native12-li1 --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r controls/li3_replay.drc -rd input=/work/week25_closure/runs/native12_stream_a/2-klayout-streamout/fault_v_asic_top.gds -rd report=/work/week25_closure/reports/native12_li1_replay.rdb > logs/native12_li1_replay.log 2>&1
