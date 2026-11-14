#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/full_fill_development.exit' EXIT
docker run --rm --name faultv-w25-full-fill --user 1000:1000 --memory=6500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/run_native_fill.py /work/week25_closure/runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds /work/week25_closure/full_fill_development > logs/full_fill_development.log 2>&1
