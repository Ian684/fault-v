#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/native_m_geometry.exit' EXIT
docker run --rm --name faultv-w25-native-m-independent --user 1000:1000 --memory=7000m --cpus=2 -e ROUTE_DRC_ODB=/runtime_final/native_group_m.odb -e ROUTE_DRC_REPORT=/work/week25_closure/reports/native_group_m_independent.json -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python /work/routing/scripts/native_route_drc.py > logs/native_group_m_independent.log 2>&1
docker run --rm --name faultv-w25-native-m-connectivity --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_all_signal_connectivity.py /runtime_final/native_group_m.odb reports/native_group_m_all_connectivity.json > logs/native_group_m_connectivity.log 2>&1
python3 scripts/prepare_m_geometry_stream.py
bash scripts/run_native_flow.sh native_m_stream_a config_native_m_stream.json native_m_stream_state.json scripts/native_librelane_cli.py 6000m 2
