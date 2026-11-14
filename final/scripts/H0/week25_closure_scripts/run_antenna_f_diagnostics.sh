#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/antenna_f_diagnostics.exit' EXIT
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-stubs-f-drc --user 1000:1000 --memory=4000m --cpus=2 -e ROUTE_DRC_ODB=/runtime_final/antenna_stubs_f.odb -e ROUTE_DRC_REPORT=/work/week25_closure/reports/antenna_stubs_f_independent.json -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python /work/routing/scripts/native_route_drc.py > logs/antenna_stubs_f_independent.log 2>&1
docker run --rm --name faultv-w25-stubs-f-connectivity --user 1000:1000 --memory=2500m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_all_signal_connectivity.py /runtime_final/antenna_stubs_f.odb reports/antenna_stubs_f_all_connectivity.json > logs/antenna_stubs_f_connectivity.log 2>&1
