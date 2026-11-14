#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/dense_b_checks.exit' EXIT
test "$(cat logs/dense_fom_native_b.exit)" = 0
docker run --rm --name faultv-w25-dense-b-compose --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" bash -c 'python3 scripts/canonicalize_fill.py dense_fom_native_b/fill_repaired.gds.gz dense_fom_native_b/canonical_fill.gds.gz && python3 scripts/compose_fill.py /runtime/fault_v_asic_top.gds dense_fom_native_b/canonical_fill.gds.gz dense_fom_native_b/filled.gds.gz && python3 scripts/check_full_fom.py /runtime/fault_v_asic_top.gds dense_fom_native_b/fill_repaired.gds.gz reports/full_fom_b_geometry.json' > logs/dense_b_compose.log 2>&1
docker run --rm --name faultv-w25-dense-b-beol --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r controls/sky130_fill_interaction_tiled.drc -rd input=/work/week25_closure/dense_fom_native_b/filled.gds.gz -rd top_cell=fault_v_asic_top -rd report=/work/week25_closure/reports/dense_b_beol.rdb > logs/dense_b_beol.log 2>&1
