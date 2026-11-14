#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/dense_fom_trial.exit' EXIT
python3 scripts/prepare_dense_fom_trial.py
docker run --rm --name faultv-w25-fom-trial --user 1000:1000 --memory=3000m --cpus=1 -e MAGTYPE=mag -v "$root:/work" -w /work/week25_closure/dense_fom_trial "$image" magic -dnull -noconsole -T /work/week25_closure/controls/sky130A-GDS-dense-FOM.tech generate_fill_dist.tcl fault_v_asic_top_fill_pattern_0_0.magx > logs/dense_fom_trial.log 2>&1
