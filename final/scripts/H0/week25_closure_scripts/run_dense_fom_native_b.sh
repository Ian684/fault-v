#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/dense_fom_native_b.exit' EXIT
docker run --rm --name faultv-w25-dense-fom-native-b --user 1000:1000 --memory=5000m --cpus=2 -e FILL_TECH_FILE=/work/week25_closure/controls/sky130A-GDS-dense-FOM-b.tech -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" python3 scripts/run_native_fill.py /runtime/fault_v_asic_top.gds /work/week25_closure/dense_fom_native_b > logs/dense_fom_native_b.log 2>&1
docker run --rm --name faultv-w25-fom-native-b-repair --user 1000:1000 --memory=4000m --cpus=1 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" python3 scripts/repair_fom_fill.py /runtime/fault_v_asic_top.gds dense_fom_native_b/fault_v_asic_top_fill_pattern.gds.gz dense_fom_native_b/fom_repaired.gds.gz reports/fom_dummy_repair_native_b.json > logs/fom_dummy_repair_native_b.log 2>&1
docker run --rm --name faultv-w25-li-native-b-repair --user 1000:1000 --memory=4000m --cpus=1 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" python3 scripts/repair_li_fill.py /runtime/fault_v_asic_top.gds dense_fom_native_b/fom_repaired.gds.gz dense_fom_native_b/fill_repaired.gds.gz reports/li_dummy_repair_native_b.json > logs/li_dummy_repair_native_b.log 2>&1
docker run --rm --name faultv-w25-dense-native-b-density --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -w /work/week25_closure "$image" python3 scripts/check_sliding_density.py /runtime/fault_v_asic_top.gds dense_fom_native_b/fill_repaired.gds.gz reports/dense_fom_native_b_density.json > logs/dense_fom_native_b_density.log 2>&1
