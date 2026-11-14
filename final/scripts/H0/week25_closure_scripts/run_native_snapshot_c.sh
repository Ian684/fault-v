#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/native_snapshot_c.exit' EXIT
docker run --rm --name faultv-w25-snapshot-c --user 1000:1000 --memory=3500m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/normalize_native_group_snapshot.py 11 native_group_c > logs/native_snapshot_c.log 2>&1
bash scripts/run_native_candidate_checks.sh native_group_c antenna_native_c
