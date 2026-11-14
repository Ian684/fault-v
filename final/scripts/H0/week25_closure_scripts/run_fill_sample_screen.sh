#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/fill_sample_screen.exit' EXIT
python3 scripts/prepare_fill_screen.py
docker run --rm --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/compose_fill.py runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds fill_tile_trial/canonical_fill.gds.gz controls/sample_fill_composite.gds.gz > logs/fill_sample_compose.log 2>&1
docker run --rm --name faultv-w25-fill-screen --user 1000:1000 --memory=3500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r controls/sky130_fill_interaction.drc -rd input=/work/week25_closure/controls/sample_fill_composite.gds.gz -rd top_cell=fault_v_asic_top -rd report=/work/week25_closure/reports/fill_sample_interaction.rdb > logs/fill_sample_screen.log 2>&1
