#!/usr/bin/env bash
# Activity targets + coverage for functional/h1c_a (H0: week25_closure/scripts/run_final_functional.sh lines 2-3).
# Usage (from cand_gap90x95, after the signoff chain's functional step passed): bash signoff/run_activity_cov_c.sh
set -uo pipefail
cd "$(dirname "$0")/.."
root="$(cd ../../.. && pwd)"; wd="/work/${PWD#$root/}"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
test "$(cat signoff/logs_c/functional.exit)" = 0 || { echo "functional did not pass"; exit 1; }
odb="$(ls runs/h1c_post/*-openroad-fillinsertion/fault_v_asic_top.odb)"
docker run --rm --name faultv-h1c-activity-targets --user 1000:1000 --memory=2500m --cpus=2 -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$root:/work" -w "$wd" "$image" openroad -exit -python signoff/export_activity_targets_c.py "$wd/$odb" h1c_a \
    > signoff/logs_c/activity_targets.log 2>&1
rc=$?; echo "targets rc=$rc"; [ "$rc" -eq 0 ] || exit "$rc"
docker run --rm --name faultv-h1c-activity-analysis --user 1000:1000 --memory=2000m --cpus=2 -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$root:/work" -w "$wd" "$image" python3 signoff/analyze_activity_h1_c.py h1c_a > signoff/logs_c/activity_analysis.log 2>&1
rc=$?; printf '%s\n' "$rc" > signoff/logs_c/activity_cov.exit; echo "analysis rc=$rc"
tail -n 5 signoff/logs_c/activity_analysis.log
exit "$rc"
