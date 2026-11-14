#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/correct_stream_checks.exit' EXIT
python3 scripts/prepare_correct_stream_checks.py
docker run --rm --name faultv-w25-correct-density --user 1000:1000 --memory=3500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r scripts/check_correct_density.py > logs/correct_density.log 2>&1
docker run --rm --name faultv-w25-correct-full-drc --user 1000:1000 --memory=5500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/correct_stream_state.json --run-tag corrected_full_drc_a config_correct_stream_checks.json > logs/correct_full_DRC.log 2>&1
