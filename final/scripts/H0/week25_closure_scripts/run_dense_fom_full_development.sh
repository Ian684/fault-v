#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/dense_fom_full.exit' EXIT
python3 - <<'PY'
import json
assert json.load(open('reports/dense_fom_trial_repaired.json'))['screen_pass']
PY
docker run --rm --name faultv-w25-dense-fom-full --user 1000:1000 --memory=4500m --cpus=2 -e FILL_TECH_FILE=/work/week25_closure/controls/sky130A-GDS-dense-FOM.tech -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/run_native_fill.py /work/week25_closure/runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds /work/week25_closure/dense_fom_full_development > logs/dense_fom_full.log 2>&1
docker run --rm --name faultv-w25-fom-island-repair --user 1000:1000 --memory=3500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/repair_fom_fill.py runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds dense_fom_full_development/fault_v_asic_top_fill_pattern.gds.gz dense_fom_full_development/fill_repaired.gds.gz reports/fom_dummy_repair_full.json > logs/fom_dummy_repair_full.log 2>&1
docker run --rm --name faultv-w25-dense-fom-density --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/check_sliding_density.py runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds dense_fom_full_development/fill_repaired.gds.gz reports/dense_fom_full_density.json > logs/dense_fom_full_density.log 2>&1
