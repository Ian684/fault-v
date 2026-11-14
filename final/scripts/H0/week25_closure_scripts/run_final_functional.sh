#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/final_functional.exit' EXIT
test "$(cat logs/focus_post_b.exit)" = 0
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-final-functional --user 1000:1000 --memory=2500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/run_closure_functional.py /work/week25_closure/runs/focus_post_b/1-openroad-fillinsertion/fault_v_asic_top.nl.v final_a > logs/final_functional.log 2>&1
docker run --rm --name faultv-w25-final-activity-targets --user 1000:1000 --memory=2500m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -w /work/week25_closure "$image" openroad -exit -python scripts/export_closure_activity_targets.py /runtime/final_filled.odb final_a > logs/final_activity_targets.log 2>&1
docker run --rm --name faultv-w25-final-activity-analysis --user 1000:1000 --memory=2000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/analyze_closure_activity.py final_a > logs/final_activity_analysis.log 2>&1
