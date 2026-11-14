#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/readonly_audits.exit' EXIT
docker run --rm --name faultv-w25-peak-vias --user 1000:1000 --memory=1800m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/inspect_peak_pg_vias.py > logs/peak_pg_vias.log 2>&1
docker run --rm --name faultv-w25-snapshot-drc-native --user 1000:1000 --memory=2500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/run_snapshot_native_check.py > logs/minimal13_independent_b.log 2>&1
