#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
task_root="$(cd .. && pwd)"
tag="${1:-floorplan_accepted}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
mkdir -p "$task_root/logs"
docker run --rm --user "$(id -u):$(id -g)" -e QT_QPA_PLATFORM=offscreen -v "$task_root:/work" -w /work/floorplan "$IMAGE" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/floorplan/initial_state.json --run-tag "$tag" config.json > "$task_root/logs/$tag.log" 2>&1
docker run --rm --user "$(id -u):$(id -g)" -e FLOORPLAN_RUN_TAG="$tag" -v "$task_root:/work" -w /work/floorplan "$IMAGE" openroad -exit -python scripts/check_floorplan.py > "$task_root/logs/${tag}_checks.log" 2>&1
