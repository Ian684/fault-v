#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
global_tag="$1"
tag="$2"
scope="${3:-routed}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
[[ "$scope" == global || "$scope" == routed ]]
root="$(cd .. && pwd)"
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
python3 scripts/check_global.py "$global_tag"
bash scripts/run_sta.sh "$tag" "$scope"
docker run --rm --user "$(id -u):$(id -g)" -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/routing "$IMAGE" openroad -no_init -no_splash -exit -python scripts/check_placement.py > "$root/logs/${tag}_check_placement.log" 2>&1
if [[ "$scope" == routed ]]; then
  docker run --rm --user "$(id -u):$(id -g)" -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/routing "$IMAGE" openroad -no_init -no_splash -exit -python scripts/check_routes.py > "$root/logs/${tag}_check_routes.log" 2>&1
  docker run --rm --user "$(id -u):$(id -g)" -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/routing "$IMAGE" openroad -no_init -no_splash -exit scripts/check_physical.tcl > "$root/logs/${tag}_physical.log" 2>&1
fi
python3 scripts/check_timing.py "$tag"
if [[ "$scope" == routed ]]; then
  python3 scripts/check_route_drc.py "$tag"
  python3 scripts/accept_phase.py "$global_tag" "$tag"
fi
echo "ALL $scope RC / CONNECTIVITY / TIMING CHECKS PASSED: $tag"
