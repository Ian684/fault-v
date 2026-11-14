#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/fill_sample_tiled.exit' EXIT
python3 scripts/prepare_tiled_fill_screen.py
docker run --rm --name faultv-w25-fill-tiled --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r controls/sky130_fill_interaction_tiled.drc -rd input=/work/week25_closure/controls/sample_fill_composite.gds.gz -rd top_cell=fault_v_asic_top -rd report=/work/week25_closure/reports/fill_sample_tiled.rdb > logs/fill_sample_tiled.log 2>&1
