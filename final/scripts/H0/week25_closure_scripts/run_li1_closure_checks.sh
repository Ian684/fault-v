#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/li1_closure_checks.exit' EXIT
python3 scripts/verify_li1_rule_replay.py
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-li1-independent --user 1000:1000 --memory=4000m --cpus=2 -e ROUTE_DRC_ODB=/runtime_final/li1_spacing.odb -e ROUTE_DRC_REPORT=/work/week25_closure/reports/li1_spacing_independent.json -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python /work/routing/scripts/native_route_drc.py > logs/li1_spacing_independent.log 2>&1
docker run --rm --name faultv-w25-li1-connectivity --user 1000:1000 --memory=3000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_all_signal_connectivity.py /runtime_final/li1_spacing.odb reports/li1_spacing_all_connectivity.json > logs/li1_spacing_connectivity.log 2>&1
python3 scripts/prepare_li1_export.py
bash scripts/run_native_flow.sh antenna_li1_a config_li1_manual.json li1_manual_state.json scripts/li1_export_cli.py 4000m 2
docker run --rm --name faultv-w25-li1-export-binding --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-native-runs/antenna_li1_a:/work/week25_closure/runs/antenna_li1_a:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_manual_export_binding.py antenna_li1_a li1_spacing_independent.json antenna_li1_a_export_binding.json > logs/antenna_li1_a_export_binding.log 2>&1
