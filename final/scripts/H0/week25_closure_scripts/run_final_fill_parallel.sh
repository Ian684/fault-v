#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/final_fill.exit' EXIT
docker run --rm --name faultv-w25-final-fill --user 1000:1000 --memory=5000m --cpus=2 -e FILL_TECH_FILE=/work/week25_closure/controls/sky130A-GDS-dense-FOM-b.tech -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -w /work/week25_closure "$image" python3 scripts/run_native_fill.py /runtime/final_core.gds /work/week25_closure/final_fill > logs/final_fill_generation.log 2>&1
docker run --rm --name faultv-w25-final-fill-repair --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -w /work/week25_closure "$image" bash -c 'set -e; python3 scripts/repair_fom_fill.py /runtime/final_core.gds final_fill/fault_v_asic_top_fill_pattern.gds.gz final_fill/fom_repaired.gds.gz reports/final_fom_repair.json; python3 scripts/repair_li_fill.py /runtime/final_core.gds final_fill/fom_repaired.gds.gz final_fill/fill_repaired.gds.gz reports/final_li_repair.json; python3 scripts/check_sliding_density.py /runtime/final_core.gds final_fill/fill_repaired.gds.gz reports/final_sliding_density.json; python3 scripts/check_dummy_grid.py final_fill/fill_repaired.gds.gz reports/final_dummy_grid.json; python3 scripts/canonicalize_fill.py final_fill/fill_repaired.gds.gz final_fill/canonical_fill.gds.gz; python3 scripts/compose_fill.py /runtime/final_core.gds final_fill/canonical_fill.gds.gz final_fill/filled.gds.gz; python3 scripts/check_full_fom.py /runtime/final_core.gds final_fill/fill_repaired.gds.gz reports/final_fom_geometry.json' > logs/final_fill_checks.log 2>&1
# Avoid the 10GiB BEOL job overlapping native IR; generation may run concurrently.
if [[ "${FINAL_FILL_WAIT_FOR_IR:-0}" = 1 ]]; then
  while [[ ! -f logs/final_ir.exit ]]; do sleep 5; done
  test "$(cat logs/final_ir.exit)" = 0
fi

docker run --rm --name faultv-w25-final-fill-beol --user 1000:1000 --memory=10000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r controls/sky130_fill_interaction_tiled.drc -rd input=/work/week25_closure/final_fill/filled.gds.gz -rd top_cell=fault_v_asic_top -rd report=/work/week25_closure/reports/final_fill_beol.rdb > logs/final_fill_beol.log 2>&1
