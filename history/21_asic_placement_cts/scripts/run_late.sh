#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
task_root="$(cd .. && pwd)"
source_tag="$1"
tag="$2"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
python3 scripts/prepare_late.py "$source_tag" "$tag"
docker run --rm --user "$(id -u):$(id -g)" -v "$task_root:/work" -w /work/placement_cts "$IMAGE" python3 -m librelane --pdk-root /work/pdk --with-initial-state "/work/placement_cts/late_state_${tag}.json" --run-tag "$tag" config_late.json > "$task_root/logs/$tag.log" 2>&1
