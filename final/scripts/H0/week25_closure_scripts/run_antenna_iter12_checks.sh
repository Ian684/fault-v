#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/antenna_iter12_checks.exit' EXIT
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-ant-iter12-probe --user 1000:1000 --memory=3500m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -v /var/tmp/faultv-w25-native-runs/antenna_route_a/1-openroad-detailedrouting:/native:ro -w /work/week25_closure "$image" openroad -exit -python scripts/probe_antenna_iter12.py > logs/antenna_iter12_probe.log 2>&1
docker run --rm --name faultv-w25-ant-iter12-drc --user 1000:1000 --memory=4500m --cpus=2 -e ROUTE_DRC_ODB=/native/drt_iter12.odb -e ROUTE_DRC_REPORT=/work/week25_closure/reports/antenna_iter12_independent.json -v "$root:/work" -v /var/tmp/faultv-w25-native-runs/antenna_route_a/1-openroad-detailedrouting:/native:ro -w /work/week25_closure "$image" openroad -exit -python /work/routing/scripts/native_route_drc.py > logs/antenna_iter12_independent.log 2>&1
docker run --rm --name faultv-w25-ant-iter12-connectivity --user 1000:1000 --memory=3000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-native-runs/antenna_route_a/1-openroad-detailedrouting:/native:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_all_signal_connectivity.py /native/drt_iter12.odb reports/antenna_iter12_all_connectivity.json > logs/antenna_iter12_connectivity.log 2>&1
